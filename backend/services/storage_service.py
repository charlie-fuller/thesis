"""Supabase Storage Service
Handles uploading, downloading, and managing files in Supabase Storage.
"""

import base64
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from supabase import Client, create_client

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing Supabase Storage operations."""

    def __init__(self):
        """Initialize Supabase client."""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv(
            "SUPABASE_SERVICE_ROLE_KEY"
        )  # Service role for admin operations

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        self.bucket_name = "conversation-images"

        logger.info("StorageService initialized")

    def ensure_bucket_exists(self) -> bool:
        """Ensure the conversation-images bucket exists.

        Note: The bucket should be created manually in Supabase dashboard.
        This just verifies it's accessible.

        Returns:
            bool: True if bucket is accessible
        """
        try:
            # Just try to access the bucket - assume it exists
            # If you get an error here, create the bucket manually in Supabase Dashboard:
            # Storage -> New Bucket -> Name: "conversation-images" -> Public: Yes
            self.client.storage.from_(self.bucket_name).list(path="", options={"limit": 1})
            return True
        except Exception as e:
            logger.error(
                f"Cannot access bucket '{self.bucket_name}'. Please create it in Supabase Dashboard: {e}",
                exc_info=True,
            )
            return False

    def upload_image(
        self, image_data: str, user_id: str, conversation_id: str, file_extension: str = "png"
    ) -> Optional[Dict[str, Any]]:
        """Upload a base64-encoded image to Supabase Storage.

        Args:
            image_data: Base64-encoded image data
            user_id: ID of the user who owns this image
            conversation_id: ID of the conversation
            file_extension: File extension (png, jpg, webp, etc.)

        Returns:
            Dict with 'storage_url', 'storage_path', and 'file_size' or None if failed
        """
        try:
            # Ensure bucket exists
            self.ensure_bucket_exists()

            # Decode base64 image
            image_bytes = base64.b64decode(image_data)
            file_size = len(image_bytes)

            # Create unique filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{conversation_id[:8]}.{file_extension}"

            # Storage path: user_id/conversation_id/filename
            # This allows easy cleanup per user/conversation
            storage_path = f"{user_id}/{conversation_id}/{filename}"

            # Determine content type
            content_type_map = {
                "png": "image/png",
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "webp": "image/webp",
                "gif": "image/gif",
            }
            content_type = content_type_map.get(file_extension.lower(), "image/png")

            # Upload to Supabase Storage
            logger.info(f"Uploading image to: {storage_path}")
            self.client.storage.from_(self.bucket_name).upload(
                path=storage_path,
                file=image_bytes,
                file_options={
                    "content-type": content_type,
                    "cache-control": "3600",  # Cache for 1 hour
                    "upsert": "false",  # Don't overwrite existing files
                },
            )

            # Get public URL - construct manually to avoid CDN issues
            # Format: https://PROJECT_REF.supabase.co/storage/v1/object/public/BUCKET/PATH
            public_url = (
                f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{storage_path}"
            )

            logger.info(f"Image uploaded successfully: {public_url}")

            return {
                "storage_url": public_url,
                "storage_path": storage_path,
                "file_size": file_size,
                "content_type": content_type,
            }

        except Exception as e:
            logger.error(f"Error uploading image to storage: {e}")
            return None

    def delete_image(self, storage_path: str) -> bool:
        """Delete an image from Supabase Storage.

        Args:
            storage_path: Path to the file in storage (e.g., "user_id/conversation_id/filename.png")

        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            logger.info(f"Deleting image from storage: {storage_path}")
            self.client.storage.from_(self.bucket_name).remove([storage_path])
            logger.info(f"Image deleted successfully: {storage_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting image from storage: {e}")
            return False

    def delete_conversation_images(self, user_id: str, conversation_id: str) -> bool:
        """Delete all images for a conversation.

        Args:
            user_id: ID of the user
            conversation_id: ID of the conversation

        Returns:
            bool: True if deleted successfully
        """
        try:
            folder_path = f"{user_id}/{conversation_id}"
            logger.info(f"Deleting all images in folder: {folder_path}")

            # List all files in the conversation folder
            files = self.client.storage.from_(self.bucket_name).list(folder_path)

            if not files:
                logger.info(f"No images found in {folder_path}")
                return True

            # Delete all files
            file_paths = [f"{folder_path}/{file['name']}" for file in files]
            self.client.storage.from_(self.bucket_name).remove(file_paths)

            logger.info(f"Deleted {len(file_paths)} images from {folder_path}")
            return True

        except Exception as e:
            logger.error(f"Error deleting conversation images: {e}")
            return False

    def get_image_url(self, storage_path: str) -> Optional[str]:
        """Get the public URL for an image.

        Args:
            storage_path: Path to the file in storage

        Returns:
            str: Public URL or None if error
        """
        try:
            # Construct URL manually to avoid CDN issues
            return f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{storage_path}"
        except Exception as e:
            logger.error(f"Error getting image URL: {e}")
            return None


# Global singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get or create the global StorageService instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
