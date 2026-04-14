"""Document Mapping Routes.

Manages the relationship between documents and system instruction template slots.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import pb_client as pb
from logger_config import get_logger
from repositories import documents as doc_repo
from validation import validate_uuid

logger = get_logger(__name__)
router = APIRouter(tags=["document_mappings"])


class DocumentMapping(BaseModel):
    template_slot: str
    document_ids: List[str]  # Can map multiple docs to one slot


class UpdateMappingsRequest(BaseModel):
    mappings: List[DocumentMapping]


class Document(BaseModel):
    id: str
    filename: str
    uploaded_at: str
    file_size: Optional[int] = None
    is_core_document: bool = False


@router.get("/api/clients/{client_id}/document-mappings")
async def get_document_mappings(client_id: str):
    """Get current document mappings for a client."""
    try:
        validate_uuid(client_id, "client_id")

        mappings = pb.get_all(
            "system_instruction_document_mappings",
            filter=f"client_id='{pb.escape_filter(client_id)}'",
            sort="template_slot",
        )

        # Group by template_slot
        mappings_by_slot: Dict[str, List[dict]] = {}
        for mapping in mappings:
            slot = mapping["template_slot"]
            if slot not in mappings_by_slot:
                mappings_by_slot[slot] = []

            doc = pb.get_record("documents", mapping["document_id"])
            if doc:
                mappings_by_slot[slot].append(
                    {
                        "mapping_id": mapping["id"],
                        "document_id": doc["id"],
                        "filename": doc.get("filename"),
                        "uploaded_at": doc.get("uploaded_at"),
                        "file_size": doc.get("file_size"),
                        "display_order": mapping.get("display_order", 0),
                    }
                )

        return {"success": True, "mappings": mappings_by_slot}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get document mappings error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.get("/api/clients/{client_id}/documents")
async def get_client_documents(client_id: str):
    """Get all documents available for mapping for a client."""
    try:
        validate_uuid(client_id, "client_id")

        documents = pb.get_all(
            "documents",
            filter="processed=true",
            sort="filename",
        )

        return {"success": True, "documents": documents}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get client documents error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/api/clients/{client_id}/document-mappings")
async def update_document_mappings(
    client_id: str, request: UpdateMappingsRequest,
):
    """Update document mappings for a client."""
    try:
        validate_uuid(client_id, "client_id")

        # Validate all document IDs
        all_doc_ids = []
        for mapping in request.mappings:
            for doc_id in mapping.document_ids:
                validate_uuid(doc_id, "document_id")
                all_doc_ids.append(doc_id)

        # Delete all existing mappings for this client
        existing = pb.get_all(
            "system_instruction_document_mappings",
            filter=f"client_id='{pb.escape_filter(client_id)}'",
        )
        for m in existing:
            pb.delete_record("system_instruction_document_mappings", m["id"])

        # Insert new mappings
        new_count = 0
        for mapping in request.mappings:
            for idx, doc_id in enumerate(mapping.document_ids):
                pb.create_record(
                    "system_instruction_document_mappings",
                    {
                        "client_id": client_id,
                        "document_id": doc_id,
                        "template_slot": mapping.template_slot,
                        "display_order": idx,
                    },
                )
                new_count += 1

        logger.info(f"Updated document mappings for client {client_id}: {new_count} mappings")

        return {"success": True, "message": f"Updated {new_count} document mappings"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update document mappings error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e


@router.post("/api/clients/{client_id}/regenerate-instructions")
async def regenerate_instructions(client_id: str):
    """Regenerate system instructions with updated document mappings."""
    try:
        validate_uuid(client_id, "client_id")

        # Import here to avoid circular dependency
        from services.solomon_stage2 import regenerate_instructions as regen

        # Get the most recent extraction for this client
        extractions = pb.get_all(
            "interview_extractions",
            filter=f"client_id='{pb.escape_filter(client_id)}'",
            sort="-created",
        )

        # Filter by valid statuses
        valid_statuses = {"extraction_complete", "instructions_generated", "approved", "deployed"}
        extraction = None
        for ext in extractions:
            if ext.get("status") in valid_statuses:
                extraction = ext
                break

        if not extraction:
            raise HTTPException(
                status_code=404,
                detail="No completed extraction found for this client. Complete an interview and extraction first.",
            )

        extraction_id = extraction["id"]

        # Regenerate instructions
        result = await regen(client_id=client_id, extraction_id=extraction_id)

        if result["status"] == "failed":
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            "success": True,
            "message": "System instructions regenerated successfully",
            "instructions_length": result["generation_metadata"]["instructions_length"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Regenerate instructions error: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred. Please try again.") from e
