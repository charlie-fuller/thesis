#!/usr/bin/env python3
"""Remote Vault Sync Client.

Local script that watches your Obsidian vault and syncs changes to the
remote Thesis backend (Railway). Runs on your local machine and uploads
file content via authenticated API calls.

Usage:
    cd backend
    python -m scripts.remote_vault_sync

Environment Variables (in .env or exported):
    REMOTE_API_URL - Railway backend URL (default: https://thesis-production.up.railway.app)
    VAULT_PATH - Path to your Obsidian vault
    SUPABASE_URL - Supabase project URL (for auth)
    SUPABASE_ANON_KEY - Supabase anon key (for auth)

You'll be prompted to log in via Supabase to get an auth token.
"""

import argparse
import getpass
import hashlib
import os
import signal
import sys
import time
from pathlib import Path
from typing import Dict, Optional

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from dotenv import load_dotenv
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

load_dotenv()

# Configuration
REMOTE_API_URL = os.getenv("REMOTE_API_URL", "https://thesis-production-badf.up.railway.app")
VAULT_PATH = os.getenv("VAULT_PATH", os.getenv("OBSIDIAN_VAULT_PATH", ""))
SUPABASE_URL = os.getenv("SUPABASE_URL", os.getenv("NEXT_PUBLIC_SUPABASE_URL", ""))
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", ""))

# File patterns - text-based files only (binary files like PDF/DOCX need multipart upload)
INCLUDE_EXTENSIONS = {
    ".md",  # Markdown
    ".txt",  # Text
    ".csv",  # CSV data (text-based)
    ".rtf",  # Rich text (text-based)
}
EXCLUDE_PATTERNS = {
    ".obsidian",
    ".trash",
    ".git",
    "node_modules",
    "__pycache__",
    ".claude",
    "_attachments",
    "_assets",
    "_backup",
    "_templates",
    "preserved-context",
    ".hypothesis",
    ".pytest_cache",
    "_excalidraw",
    "_resources",
    "_scratch",
    "Attachments",
    "Backups",
    "Daily Notes",
    "GitHub/thesis",
    "logseq",
    "Templates",
}

# Debounce settings
DEBOUNCE_SECONDS = 2.0
MAX_FILE_SIZE_MB = 5  # Only sync files under this size


class RemoteVaultSyncer:
    """Syncs local vault changes to remote API by uploading file content."""

    def __init__(self, api_url: str, vault_path: str, auth_token: str):
        self.api_url = api_url.rstrip("/")
        self.vault_path = Path(vault_path)
        self.auth_token = auth_token
        self.client = httpx.Client(timeout=60.0)
        self._pending_files: Dict[str, float] = {}
        self._file_hashes: Dict[str, str] = {}
        self._running = True
        self._synced_count = 0
        self._error_count = 0

    def _get_headers(self) -> dict:
        """Get auth headers for API requests."""
        return {"Authorization": f"Bearer {self.auth_token}", "Content-Type": "application/json"}

    def _should_sync(self, file_path: Path) -> bool:
        """Check if file should be synced."""
        # Check extension
        if file_path.suffix.lower() not in INCLUDE_EXTENSIONS:
            return False

        # Check excluded patterns
        path_str = str(file_path)
        for pattern in EXCLUDE_PATTERNS:
            if f"/{pattern}/" in path_str or path_str.endswith(f"/{pattern}"):
                return False
            if pattern in file_path.parts:
                return False

        # Check file size
        try:
            if file_path.stat().st_size > MAX_FILE_SIZE_MB * 1024 * 1024:
                return False
        except OSError:
            return False

        return True

    def _compute_hash(self, file_path: Path) -> str:
        """Compute MD5 hash of file."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def _read_file(self, file_path: Path) -> Optional[str]:
        """Read file content as text."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with latin-1 as fallback
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    return f.read()
            except Exception:
                return None
        except Exception:
            return None

    def check_status(self) -> dict:
        """Check connection to remote API."""
        try:
            response = self.client.get(
                f"{self.api_url}/api/obsidian/status", headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            return {"connected": False, "error": f"HTTP {e.response.status_code}"}
        except Exception as e:
            return {"connected": False, "error": str(e)}

    def upload_file(self, file_path: Path) -> dict:
        """Upload a single file to remote API."""
        relative_path = str(file_path.relative_to(self.vault_path))

        # Read file content
        content = self._read_file(file_path)
        if content is None:
            return {"success": False, "error": "Could not read file"}

        # Check if changed
        new_hash = hashlib.md5(content.encode()).hexdigest()
        old_hash = self._file_hashes.get(relative_path, "")

        if new_hash == old_hash:
            return {"success": True, "status": "unchanged"}

        # Determine content type
        ext = file_path.suffix.lower()
        content_type = "text/markdown" if ext == ".md" else "text/plain"

        try:
            response = self.client.post(
                f"{self.api_url}/api/obsidian/upload",
                headers=self._get_headers(),
                json={"file_path": relative_path, "content": content, "content_type": content_type},
            )
            response.raise_for_status()
            result = response.json()

            if result.get("success"):
                self._file_hashes[relative_path] = new_hash
                self._synced_count += 1

            return result

        except httpx.HTTPStatusError as e:
            self._error_count += 1
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text[:100]}",
            }
        except Exception as e:
            self._error_count += 1
            return {"success": False, "error": str(e)}

    def queue_file(self, file_path: Path):
        """Queue file for debounced sync."""
        if self._should_sync(file_path):
            relative_path = str(file_path.relative_to(self.vault_path))
            self._pending_files[relative_path] = time.time()

    def process_pending(self):
        """Process pending file changes after debounce."""
        now = time.time()
        ready_files = []

        for path, queued_time in list(self._pending_files.items()):
            if now - queued_time >= DEBOUNCE_SECONDS:
                ready_files.append(path)
                del self._pending_files[path]

        for relative_path in ready_files:
            file_path = self.vault_path / relative_path
            if file_path.exists():
                print(f"  Syncing: {relative_path}...", end=" ", flush=True)
                result = self.upload_file(file_path)
                status = result.get("status", result.get("error", "unknown"))
                print(status)

    def initial_sync(self, limit: int = 100):
        """Sync recently modified files on startup."""
        print("\nScanning vault for recent files...")

        # Find all eligible files
        files = []
        for ext in INCLUDE_EXTENSIONS:
            for file_path in self.vault_path.rglob(f"*{ext}"):
                if self._should_sync(file_path):
                    try:
                        mtime = file_path.stat().st_mtime
                        files.append((file_path, mtime))
                    except OSError:
                        continue

        # Sort by modification time, most recent first
        files.sort(key=lambda x: x[1], reverse=True)

        # Sync top N files
        files_to_sync = files[:limit]
        print(f"Found {len(files)} eligible files, syncing {len(files_to_sync)} most recent...\n")

        for i, (file_path, _) in enumerate(files_to_sync, 1):
            relative_path = str(file_path.relative_to(self.vault_path))
            print(f"  [{i}/{len(files_to_sync)}] {relative_path}...", end=" ", flush=True)
            result = self.upload_file(file_path)
            status = result.get("status", result.get("error", "unknown"))
            print(status)

        print(f"\nInitial sync complete: {self._synced_count} synced, {self._error_count} errors")

    def run_watcher(self):
        """Run the file watcher loop."""

        class Handler(FileSystemEventHandler):
            def __init__(handler_self, syncer):
                handler_self.syncer = syncer

            def on_created(handler_self, event):
                if not event.is_directory:
                    handler_self.syncer.queue_file(Path(event.src_path))

            def on_modified(handler_self, event):
                if not event.is_directory:
                    handler_self.syncer.queue_file(Path(event.src_path))

            def on_deleted(handler_self, event):
                if not event.is_directory:
                    relative = str(Path(event.src_path).relative_to(handler_self.syncer.vault_path))
                    print(f"  Deleted (not synced): {relative}")

        observer = Observer()
        observer.schedule(Handler(self), str(self.vault_path), recursive=True)
        observer.start()

        print(f"\nWatching: {self.vault_path}")
        print("Press Ctrl+C to stop\n")

        try:
            while self._running:
                self.process_pending()
                time.sleep(0.5)
        except KeyboardInterrupt:
            pass
        finally:
            observer.stop()
            observer.join()
            print(f"\nStopped. Total synced: {self._synced_count}, errors: {self._error_count}")

    def stop(self):
        """Stop the watcher."""
        self._running = False


TOKEN_FILE = Path.home() / ".thesis" / "vault_sync_token.json"


def save_auth_tokens(access_token: str, refresh_token: str):
    """Save auth tokens to file for persistent use."""
    TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    import json

    with open(TOKEN_FILE, "w") as f:
        json.dump({"access_token": access_token, "refresh_token": refresh_token}, f)
    TOKEN_FILE.chmod(0o600)  # Secure permissions
    print(f"  Tokens saved to {TOKEN_FILE}")


def load_auth_tokens() -> Optional[Dict[str, str]]:
    """Load saved auth tokens."""
    if not TOKEN_FILE.exists():
        return None
    try:
        import json

        with open(TOKEN_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return None


def refresh_auth_token(refresh_token: str) -> Optional[Dict[str, str]]:
    """Refresh access token using refresh token."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        return None
    try:
        client = httpx.Client()
        response = client.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
            headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
            json={"refresh_token": refresh_token},
        )
        response.raise_for_status()
        data = response.json()
        return {
            "access_token": data.get("access_token"),
            "refresh_token": data.get("refresh_token", refresh_token),
        }
    except Exception as e:
        print(f"Token refresh failed: {e}")
        return None


def get_auth_token(interactive: bool = True) -> Optional[str]:
    """Get auth token - tries saved token first, then prompts if needed."""
    # Try loading saved tokens
    saved = load_auth_tokens()
    if saved:
        print("  Found saved auth tokens, refreshing...")
        refreshed = refresh_auth_token(saved.get("refresh_token", ""))
        if refreshed and refreshed.get("access_token"):
            save_auth_tokens(refreshed["access_token"], refreshed["refresh_token"])
            print("  Token refreshed successfully!")
            return refreshed["access_token"]
        print("  Saved tokens expired or invalid.")

    if not interactive:
        print("ERROR: No valid saved token and running non-interactively.")
        print(f"Run once interactively to authenticate, or provide --token")
        return None

    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("ERROR: SUPABASE_URL and SUPABASE_ANON_KEY required for authentication")
        print("Set these in your .env file or environment")
        return None

    print("\n=== Supabase Authentication ===")
    print("Enter your Thesis login credentials:\n")

    email = input("Email: ").strip()
    password = getpass.getpass("Password: ")

    try:
        client = httpx.Client()
        response = client.post(
            f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
            json={"email": email, "password": password},
        )
        response.raise_for_status()
        data = response.json()
        access_token = data.get("access_token")
        refresh_token = data.get("refresh_token")
        if access_token:
            print("Authentication successful!")
            if refresh_token:
                save_auth_tokens(access_token, refresh_token)
        return access_token
    except httpx.HTTPStatusError as e:
        print(f"Authentication failed: {e.response.text}")
        return None
    except Exception as e:
        print(f"Authentication error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Sync local vault to remote Thesis backend (Railway)"
    )
    parser.add_argument("--vault-path", default=VAULT_PATH, help="Path to Obsidian vault")
    parser.add_argument(
        "--api-url",
        default=REMOTE_API_URL,
        help="Remote API URL (default: thesis-production-badf.up.railway.app)",
    )
    parser.add_argument("--token", help="Auth token (will prompt if not provided)")
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run as daemon (non-interactive, uses saved token)",
    )
    parser.add_argument(
        "--initial-sync",
        type=int,
        default=50,
        metavar="N",
        help="Number of recent files to sync on startup (default: 50, 0 to skip)",
    )
    parser.add_argument(
        "--watch-only", action="store_true", help="Only watch for changes, skip initial sync"
    )

    args = parser.parse_args()

    if not args.vault_path:
        print("ERROR: Vault path required. Set VAULT_PATH env var or use --vault-path")
        sys.exit(1)

    vault_path = Path(args.vault_path)
    if not vault_path.exists():
        print(f"ERROR: Vault path does not exist: {vault_path}")
        sys.exit(1)

    print(f"\n{'='*50}")
    print("  Remote Vault Sync Client")
    print(f"{'='*50}")
    print(f"API:   {args.api_url}")
    print(f"Vault: {vault_path}")

    # Get auth token
    token = args.token or get_auth_token(interactive=not args.daemon)
    if not token:
        print("\nERROR: Could not get auth token")
        if args.daemon:
            print("Run once without --daemon to authenticate and save token.")
        sys.exit(1)

    # Create syncer
    syncer = RemoteVaultSyncer(args.api_url, str(vault_path), token)

    # Check connection
    print("\nChecking connection...")
    status = syncer.check_status()
    if status.get("connected"):
        print(f"  Connected to vault: {status.get('vault_name')}")
        print(f"  Files synced: {status.get('files_synced', 0)}")
    elif "error" in status:
        print(f"  Connection issue: {status.get('error')}")
        print("  Will attempt to sync anyway...")
    else:
        print("  Vault not configured on remote. Will create documents.")

    # Set up signal handler
    def signal_handler(sig, frame):
        print("\n\nShutting down...")
        syncer.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initial sync
    if not args.watch_only and args.initial_sync > 0:
        syncer.initial_sync(limit=args.initial_sync)

    # Run watcher
    print("\nStarting file watcher...")
    syncer.run_watcher()


if __name__ == "__main__":
    main()
