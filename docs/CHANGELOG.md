# Thesis Development Changelog

This document contains historical development notes, detailed technical updates, and implementation details that were previously in the main README. For current project overview, see the [main README](../README.md).

---

## December 2024 Updates

### Image Generation UX & State Management (December 19, 2024)

**Image Options Dialog:**
- Aspect Ratio & Quality Selection - Users now see an inline dialog to choose aspect ratio (1:1, 16:9, 9:16, 4:3) and quality (Fast or Quality) before image generation begins
- Regenerate Button Fixed - The regenerate button on images now properly shows the options dialog instead of doing nothing
- Real-time SSE Events - New `image_suggestion` event streams to frontend immediately, no page refresh needed

**Context & State Management Fixes:**
- Prevented Context Confusion - Fixed critical bug where saying "hello" after an image suggestion caused the assistant to respond with completely unrelated content from earlier in the conversation
- Proper State Cleanup - All pending states (`awaiting_image_confirmation`) are now explicitly cleared on:
  - User confirmation - Generate image
  - User decline ("no", "cancel", "skip")
  - User greeting ("hello", "hi")
  - User changes topic (any other message)
  - Error during generation
- Metadata Format Compatibility - Fixed mismatch between old (`suggested_visual_type`) and new (`image_suggestion.suggested_prompt`) metadata formats

**Image Request Flow Improvements:**
- Lowered Word Threshold - Short but specific requests like "a chicken that looks like a pigeon" (7 words) now work correctly instead of falling back to conversation history
- Direct Message Processing - Explicit image requests with content are processed directly instead of analyzing conversation history
- Removed Over-Engineering - Simplified context handling to trust Claude's native capabilities instead of adding complex guardrails

**Technical Details:**
- State transitions fully documented: IDLE - AWAITING_CONFIRMATION - (confirm/decline/greeting/other/error) - IDLE or GENERATING
- Empty placeholder messages from image flows are now skipped when building conversation history
- All exit paths from pending states are logged for debugging

### Bug Fixes & Stability (December 16-17, 2024)

**Document Search (RAG) Improvements:**
- Document Reference Detection - New query type `document_reference` with permissive threshold (0.15) for queries explicitly mentioning uploaded documents like "tell me about this document" or "the file I uploaded"
- Honest Failure Messaging - When RAG search finds no relevant documents, Thesis now provides helpful feedback about possible causes (processing delay, wording mismatch, no uploads yet) instead of silently falling back to general knowledge
- Vector Search Now Working - Fixed RPC parameter mismatch between backend code and database function. Search now correctly calls `match_document_chunks` with proper parameters.
- Lowered Similarity Thresholds - Reduced from 0.5/0.4 to 0.3/0.25 for factual/exploratory queries to allow semantic matches with natural language queries.
- Added Debug Logging - Search function now logs query details, embedding length, result count, and top similarity scores for easier troubleshooting.

**Chat Interface Fixes:**
- Message Disappearing Bug Fixed - Messages no longer vanish when starting a new conversation. Added `isSendingFirstMessage` state to prevent `loadConversation()` from overwriting frontend state during conversation creation.
- Invalid Date Display Fixed - Chat timestamps now display correctly. Backend returns `created_at` field which frontend now properly maps to `timestamp`.

**User Profile Features:**
- Avatar Upload/Delete - New endpoints for user avatar management with Supabase Storage integration

**System Prompt Updates:**
- Simplified System Prompt v1.1 - Streamlined prompt with "Knowledge Base First" criterion, added image generation capability, removed verbose/redundant sections

**Database Migrations:**
- Google Drive Sync Cadence - Added `sync_frequency`, `last_auto_sync`, `next_sync_scheduled` columns to `google_drive_tokens` table (migration 012).

### Image Generation System Overhaul

Complete rebuild of the image generation pipeline with significant performance and UX improvements:

**Performance:**
- 3-5 second generation time - Using Google's gemini-2.5-flash-image model (nano banana)
- Automatic detection - System recognizes image requests from natural language
- Real-time streaming - Images generate while users continue conversing
- Reliable storage - Direct Supabase integration with automatic URL management

**User Experience:**
- Visual feedback - Animated loading placeholder shows "Generating image..." during creation
- Chronological timeline - Messages and images display in perfect sequence
- Multiple images - Generate unlimited images per conversation with proper ordering
- Instant display - Images appear inline immediately after generation

**Technical Architecture:**
- HTTP REST API - Switched from SDK to direct API calls for better control
- Direct storage URLs - Fixed CDN issues by using Supabase project URLs
- Database integration - Full metadata tracking with foreign key constraints
- Type safety - Complete TypeScript integration across frontend and backend

---

## Image Generation Pipeline Development (December 2024)

Complete rebuild of the image generation system with focus on performance, reliability, and UX:

**Technical Challenges Solved:**
1. CDN Resolution Issues - Migrated from Supabase CDN URLs to direct project URLs to eliminate `gygax-files.com` DNS errors
2. Timeline Ordering - Implemented chronological merge of messages and orphaned images using timestamp-based sorting
3. TypeScript Type Safety - Added `imageLoading` and `imageId` properties to Message interface across local and global type definitions
4. Database Schema - Added `metadata` JSONB column to messages table with GIN index for image suggestions
5. Loading State Management - Built animated placeholder system with React state management for visual feedback
6. API Architecture - Switched from Python SDK to direct HTTP REST API for better control and error handling
7. Foreign Key Constraints - Implemented proper relationships between conversations, messages, and images tables
8. Streaming Integration - Added `image_generated` SSE event type to notify frontend of completion

**Code Quality Improvements:**
- Full type safety across frontend (TypeScript) and backend (Python type hints)
- Comprehensive error handling with user-friendly messages
- Structured logging for debugging and monitoring
- Database migrations with proper rollback support
- Automatic schema cache reloading via PostgreSQL NOTIFY

**Performance Optimizations:**
- Reduced image generation time from 10-15s to 3-5s by switching models
- Parallel processing: images generate while conversation continues
- Optimized database queries with proper indexes
- Client-side caching of conversation images
- Lazy loading of image data only when needed

**Testing & Validation:**
- End-to-end integration tests for complete flow
- Direct API tests bypassing service layer
- Storage bucket verification and backfill scripts
- Production deployment verification on Railway and Vercel

---

## Related Documentation

- [Image Generation Setup Guide](./IMAGE_GENERATION_SETUP.md) - Complete setup for Nano Banana (Google Gemini)
- [Deployment Guide](./deployment/DEPLOYMENT_GUIDE.md) - Railway and Vercel deployment
- [System Instructions](./system-instructions/) - Thesis L&D persona configuration

---

**Last Updated:** December 2024
