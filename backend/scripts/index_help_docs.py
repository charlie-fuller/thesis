"""
Index Help Documentation Script (v2 - with title/heading context)

Processes markdown files from docs/help/ into the help_documents and help_chunks tables
with embeddings for RAG-powered help chat.

Embeddings now include document title and section heading for better semantic search.

Usage:
    python backend/scripts/index_help_docs.py
    python backend/scripts/index_help_docs.py --force  # Reindex all docs
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import get_supabase
from logger_config import get_logger
from services.embeddings import create_embedding

logger = get_logger(__name__)
supabase = get_supabase()

# Base path for help docs
# On Railway: backend/docs_help is committed directly in the repo
# Local dev: docs/help at repo root is the source of truth
def get_help_docs_path():
    """Find the help docs path."""
    script_path = Path(__file__).resolve()
    cwd = Path.cwd().resolve()

    # Option 1: backend/docs_help (committed in repo, works on Railway)
    backend_docs_help = script_path.parent.parent / "docs_help"
    if backend_docs_help.exists():
        return backend_docs_help

    # Option 2: From script location to repo root -> docs/help/ (local dev)
    repo_root_from_script = script_path.parent.parent.parent / "docs" / "help"
    if repo_root_from_script.exists():
        return repo_root_from_script

    # Option 3: cwd/docs_help (if running from backend folder)
    cwd_docs_help = cwd / "docs_help"
    if cwd_docs_help.exists():
        return cwd_docs_help

    # Option 4: Parent of cwd -> docs/help (local dev from backend folder)
    cwd_parent_docs = cwd.parent / "docs" / "help"
    if cwd_parent_docs.exists():
        return cwd_parent_docs

    # Fallback
    logger.warning("Help docs not found!")
    return backend_docs_help

HELP_DOCS_PATH = get_help_docs_path()

# Role access mapping based on directory
ROLE_ACCESS_MAP = {
    "admin": ["admin"],
    "system": ["admin", "user"],  # System understanding useful for both
    "user": ["user"],
    "technical": ["admin"]  # Technical details admin-only
}

CHUNK_SIZE = 1000  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks


def extract_markdown_sections(content: str) -> List[Tuple[str, str]]:
    """
    Split markdown content into sections based on headings.

    Args:
        content: Full markdown content

    Returns:
        List of (heading, content) tuples
    """
    sections = []
    current_heading = "Introduction"
    current_content = []

    for line in content.split('\n'):
        # Check if line is a heading (starts with #)
        if line.strip().startswith('#'):
            # Save previous section
            if current_content:
                sections.append((current_heading, '\n'.join(current_content)))

            # Start new section
            current_heading = line.strip().lstrip('#').strip()
            current_content = []
        else:
            current_content.append(line)

    # Add final section
    if current_content:
        sections.append((current_heading, '\n'.join(current_content)))

    return sections


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Text to chunk
        chunk_size: Max characters per chunk
        overlap: Characters to overlap between chunks

    Returns:
        List of text chunks
    """
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence end markers within last 100 chars
            sentence_end = max(
                text.rfind('. ', start, end),
                text.rfind('.\n', start, end),
                text.rfind('? ', start, end),
                text.rfind('! ', start, end)
            )
            if sentence_end > start + chunk_size - 100:  # Found reasonable break point
                end = sentence_end + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap if end < len(text) else len(text)

    return chunks


def process_document(file_path: Path, force: bool = False) -> Dict:
    """
    Process a single markdown document into help_documents and help_chunks.

    Args:
        file_path: Path to markdown file
        force: If True, reindex even if already exists

    Returns:
        Dict with processing stats
    """
    logger.info(f"Processing {file_path}")

    # Read file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract metadata
    relative_path = str(file_path.relative_to(HELP_DOCS_PATH))
    category = relative_path.split('/')[0]  # admin, system, user, technical
    title = file_path.stem.replace('-', ' ').title()  # Convert filename to title

    # Check if already indexed
    existing = supabase.table('help_documents').select('id, updated_at').eq(
        'file_path', relative_path
    ).execute()

    document_id = None

    if existing.data and not force:
        logger.info(f"Document {relative_path} already indexed, skipping")
        return {
            "status": "skipped",
            "file_path": relative_path,
            "reason": "already_exists"
        }
    elif existing.data and force:
        # Update existing document
        document_id = existing.data[0]['id']
        logger.info(f"Reindexing {relative_path}")

        # Delete old chunks
        supabase.table('help_chunks').delete().eq('document_id', document_id).execute()

        # Update document
        supabase.table('help_documents').update({
            'content': content,
            'word_count': len(content.split()),
            'updated_at': 'NOW()'
        }).eq('id', document_id).execute()
    else:
        # Create new document
        result = supabase.table('help_documents').insert({
            'title': title,
            'file_path': relative_path,
            'category': category,
            'role_access': ROLE_ACCESS_MAP.get(category, ['admin', 'user']),
            'content': content,
            'word_count': len(content.split())
        }).execute()

        document_id = result.data[0]['id']
        logger.info(f"Created new document {relative_path}")

    # Extract sections from markdown
    sections = extract_markdown_sections(content)

    # Process each section into chunks
    chunks_created = 0
    chunk_index = 0

    for heading, section_content in sections:
        # Chunk the section content
        section_chunks = chunk_text(section_content)

        for chunk_text_content in section_chunks:
            # Skip very short chunks (likely just whitespace)
            if len(chunk_text_content.strip()) < 50:
                continue

            # Generate embedding
            try:
                # Prepend document title and section heading for better semantic context
                embedding_content = f"{title} - {heading}\n\n{chunk_text_content}"
                embedding = create_embedding(embedding_content, input_type="document")

                # Insert chunk
                supabase.table('help_chunks').insert({
                    'document_id': document_id,
                    'content': chunk_text_content,
                    'embedding': embedding,
                    'chunk_index': chunk_index,
                    'heading_context': heading,
                    'role_access': ROLE_ACCESS_MAP.get(category, ['admin', 'user']),
                    'metadata': {
                        'category': category,
                        'title': title,
                        'section': heading
                    }
                }).execute()

                chunks_created += 1
                chunk_index += 1

            except Exception as e:
                logger.error(f"Error creating embedding for chunk {chunk_index}: {e}")
                continue

    logger.info(f"Created {chunks_created} chunks for {relative_path}")

    return {
        "status": "success",
        "file_path": relative_path,
        "document_id": document_id,
        "chunks_created": chunks_created
    }


def index_all_help_docs(force: bool = False, progress_callback=None):
    """
    Index all markdown files in docs/help/ directory.

    Args:
        force: If True, reindex all documents even if they exist
        progress_callback: Optional callback function(progress_pct, current_file) for progress updates
    """
    logger.info("Starting help documentation indexing")
    logger.info(f"Help docs path: {HELP_DOCS_PATH}")
    logger.info(f"Force reindex: {force}")

    # If force is True, delete ALL existing data first to ensure fresh embeddings
    if force:
        logger.info("Force mode: Deleting all existing chunks and documents for fresh reindex...")
        try:
            # Delete chunks first (foreign key constraint)
            supabase.table('help_chunks').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            logger.info("All existing chunks deleted")
            # Delete documents too so they get fully recreated
            supabase.table('help_documents').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            logger.info("All existing documents deleted")
        except Exception as e:
            logger.error(f"Error deleting data: {e}")

    if not HELP_DOCS_PATH.exists():
        logger.error(f"Help docs path does not exist: {HELP_DOCS_PATH}")
        return

    # Find all markdown files
    markdown_files = list(HELP_DOCS_PATH.glob("**/*.md"))
    logger.info(f"Found {len(markdown_files)} markdown files")

    stats = {
        "total_files": len(markdown_files),
        "processed": 0,
        "skipped": 0,
        "errors": 0,
        "total_chunks": 0
    }

    # Process each file
    for i, md_file in enumerate(markdown_files):
        try:
            # Report progress
            if progress_callback:
                progress_pct = int((i / len(markdown_files)) * 100)
                progress_callback(progress_pct, md_file.name)

            result = process_document(md_file, force=force)

            if result["status"] == "success":
                stats["processed"] += 1
                stats["total_chunks"] += result["chunks_created"]
            elif result["status"] == "skipped":
                stats["skipped"] += 1

        except Exception as e:
            logger.error(f"Error processing {md_file}: {e}")
            stats["errors"] += 1

    # Final progress update
    if progress_callback:
        progress_callback(100, "Complete")

    # Print summary
    logger.info("=" * 50)
    logger.info("INDEXING COMPLETE")
    logger.info("=" * 50)
    logger.info(f"Total files: {stats['total_files']}")
    logger.info(f"Processed: {stats['processed']}")
    logger.info(f"Skipped: {stats['skipped']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info(f"Total chunks created: {stats['total_chunks']}")
    logger.info("=" * 50)

    # Verify in database
    doc_count = supabase.table('help_documents').select('id', count='exact').execute()
    chunk_count = supabase.table('help_chunks').select('id', count='exact').execute()

    logger.info("Database verification:")
    logger.info(f"  Documents in DB: {doc_count.count}")
    logger.info(f"  Chunks in DB: {chunk_count.count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Index help documentation for RAG search")
    parser.add_argument(
        '--force',
        action='store_true',
        help="Reindex all documents even if they already exist"
    )

    args = parser.parse_args()

    try:
        index_all_help_docs(force=args.force)
    except KeyboardInterrupt:
        logger.info("\nIndexing interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error during indexing: {e}")
        sys.exit(1)
