"""Theme Settings API Routes.

Endpoints for managing application theme/styling settings.
"""

import uuid
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

import pb_client as pb
from logger_config import get_logger

router = APIRouter(tags=["Theme"])
logger = get_logger(__name__)


class ThemeSettings(BaseModel):
    """Theme settings model."""

    # Brand colors
    color_primary: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    color_primary_hover: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    color_secondary: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    color_text_on_primary: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    color_text_on_secondary: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")

    # Background colors
    color_bg_page: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    color_bg_card: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    color_bg_hover: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")

    # Text colors
    color_text_primary: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    color_text_secondary: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    color_text_muted: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")

    # Border colors
    color_border: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    color_border_focus: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")

    # Status colors
    color_success: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    color_warning: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    color_error: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")

    # Typography
    font_family_heading: Optional[str] = None
    font_weight_heading: Optional[str] = None
    font_family_body: Optional[str] = None
    font_weight_body: Optional[str] = None
    font_size_base: Optional[str] = None

    # Border radius
    border_radius_sm: Optional[str] = None
    border_radius_md: Optional[str] = None
    border_radius_lg: Optional[str] = None

    # Panel/Card edge styling
    panel_border_width: Optional[str] = None
    panel_border_color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    panel_shadow_size: Optional[str] = None
    panel_shadow_color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")

    # Header styling
    header_logo_url: Optional[str] = None
    header_bg_color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    header_title_color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    header_nav_color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    header_nav_active_color: Optional[str] = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    header_font_size: Optional[str] = None
    header_height: Optional[str] = None
    page_title_font_size: Optional[str] = None


@router.get("/api/theme")
async def get_theme_settings():
    """Get theme settings for the application."""
    try:
        # Single-tenant: get the first (only) theme record
        result = pb.get_first("theme_settings")

        if not result:
            # Return default theme if none exists
            return {"success": True, "theme": get_default_theme()}

        return {"success": True, "theme": result}

    except Exception as e:
        logger.error(f"Error fetching theme settings: {e}")
        # Return default theme on error
        return {"success": True, "theme": get_default_theme()}


@router.put("/api/theme")
async def update_theme_settings(settings: ThemeSettings):
    """Update theme settings."""
    try:
        # Build update data, excluding None values
        update_data = {k: v for k, v in settings.dict().items() if v is not None}

        if not update_data:
            raise HTTPException(status_code=400, detail="No settings provided")

        # Check if theme settings exist
        existing = pb.get_first("theme_settings", fields="id")

        if existing:
            # Update existing
            result = pb.update_record("theme_settings", existing["id"], update_data)
        else:
            # Insert new
            result = pb.create_record("theme_settings", update_data)

        logger.info("Theme settings updated")

        return {
            "success": True,
            "message": "Theme settings updated",
            "theme": result if result else update_data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating theme settings: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/api/theme/reset")
async def reset_theme_settings():
    """Reset theme settings to defaults."""
    try:
        default_theme = get_default_theme()

        # Remove non-column fields
        default_theme.pop("id", None)
        default_theme.pop("created", None)
        default_theme.pop("updated", None)

        # Try update existing, else create
        existing = pb.get_first("theme_settings", fields="id")

        if existing:
            result = pb.update_record("theme_settings", existing["id"], default_theme)
        else:
            result = pb.create_record("theme_settings", default_theme)

        logger.info("Theme settings reset")

        return {
            "success": True,
            "message": "Theme settings reset to defaults",
            "theme": result if result else default_theme,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting theme settings: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


ALLOWED_LOGO_TYPES = ["image/png", "image/jpeg", "image/gif", "image/svg+xml", "image/webp"]
MAX_LOGO_SIZE = 2 * 1024 * 1024  # 2MB


@router.post("/api/theme/logo")
async def upload_logo(file: UploadFile = File(...)):
    """Upload a logo image.

    TODO: PocketBase file upload -- needs PB file API integration.
    Currently stores metadata only.
    """
    try:
        # Validate file type
        if file.content_type not in ALLOWED_LOGO_TYPES:
            raise HTTPException(status_code=400, detail="Invalid file type. Allowed: PNG, JPEG, GIF, SVG, WebP")

        # Read and validate file size
        file_content = await file.read()
        if len(file_content) > MAX_LOGO_SIZE:
            raise HTTPException(status_code=400, detail="Logo file too large. Maximum size is 2MB")

        # Generate unique filename
        file_ext = file.filename.split(".")[-1] if "." in file.filename else "png"
        unique_filename = f"logo_{uuid.uuid4()}.{file_ext}"

        # TODO: Upload to PocketBase file storage
        # For now, store a placeholder URL
        logo_url = f"/api/files/logos/{unique_filename}"

        # Update theme settings with new logo URL
        existing = pb.get_first("theme_settings", fields="id")

        if existing:
            pb.update_record("theme_settings", existing["id"], {"header_logo_url": logo_url})
        else:
            pb.create_record("theme_settings", {"header_logo_url": logo_url})

        logger.info("Logo uploaded successfully")

        return {"success": True, "message": "Logo uploaded successfully", "logo_url": logo_url}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading logo: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.delete("/api/theme/logo")
async def delete_logo():
    """Remove the logo."""
    try:
        # Set logo URL to null
        existing = pb.get_first("theme_settings", fields="id")

        if existing:
            pb.update_record("theme_settings", existing["id"], {"header_logo_url": None})

        logger.info("Logo removed")

        return {"success": True, "message": "Logo removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing logo: {e}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


def get_default_theme() -> dict:
    """Return default theme settings."""
    return {
        "color_primary": "#6366f1",
        "color_primary_hover": "#4f46e5",
        "color_secondary": "#8b5cf6",
        "color_text_on_primary": "#ffffff",
        "color_text_on_secondary": "#ffffff",
        "color_bg_page": "#0a0a0a",
        "color_bg_card": "#111111",
        "color_bg_hover": "#1a1a1a",
        "color_text_primary": "#ffffff",
        "color_text_secondary": "#a1a1aa",
        "color_text_muted": "#71717a",
        "color_border": "#27272a",
        "color_border_focus": "#6366f1",
        "color_success": "#22c55e",
        "color_warning": "#f59e0b",
        "color_error": "#ef4444",
        "font_family_heading": "Inter",
        "font_weight_heading": "600",
        "font_family_body": "Inter",
        "font_weight_body": "400",
        "font_size_base": "16px",
        "border_radius_sm": "0.25rem",
        "border_radius_md": "0.5rem",
        "border_radius_lg": "0.75rem",
        "panel_border_width": "1px",
        "panel_border_color": "#27272a",
        "panel_shadow_size": "1px",
        "panel_shadow_color": "#000000",
        "header_logo_url": None,
        "header_bg_color": "#111111",
        "header_title_color": "#14b8a6",
        "header_nav_color": "#a1a1aa",
        "header_nav_active_color": "#14b8a6",
        "header_font_size": "20px",
        "header_height": "64px",
        "page_title_font_size": "32px",
    }
