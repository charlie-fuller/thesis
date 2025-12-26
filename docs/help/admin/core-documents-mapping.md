# Core Documents Mapping

This guide explains how to configure which documents Thesis references in its AI system instructions through the Core Documents Mapping feature.

## What Are Core Document Mappings?

Core Document Mappings allow you to specify which uploaded documents Thesis should reference when responding to users. By mapping documents to template slots, you control:

- What frameworks and methodologies Thesis follows
- What domain expertise Thesis draws from
- What writing style Thesis uses
- What examples Thesis can reference

When you map a document, the AI's system instructions are updated to explicitly reference that document by name.

## Accessing Core Documents

### From User Detail Page

1. Navigate to **Dashboard** → **Users**
2. Click **View Details** for any user
3. In the **Overview** tab, find **Core Document Mappings**
4. Click **Manage Core Documents**

This opens the **Link Reference Documents** page.

## The Core Documents Page

### Page Header

The page displays:
- **← Back to Solomon Review** - Link to return
- **Link Reference Documents** - Page title
- Subtitle: "Map uploaded documents to AI instruction templates for [clientName]"
- **Last updated:** timestamp (if mappings exist)

### Action Buttons

Two buttons at the top right:
- **Save Mappings** - Save your document selections
- **Regenerate Instructions** - Rebuild AI instructions with current mappings

## Understanding Template Slots

The page shows five template slots where you can assign documents. Each slot serves a specific purpose in shaping Thesis's responses.

### Project Management Models

**Description:** "Frameworks like Agile, OKRs, Eisenhower Matrix"

Map documents that describe:
- Project management methodologies
- Productivity frameworks
- Planning and prioritization systems
- Team coordination approaches

**Example documents:**
- company-agile-guide.pdf
- okr-framework.docx
- project-planning-handbook.pdf

### Domain-Specific Models

**Description:** "Industry or field-specific frameworks"

Map documents that cover:
- Industry-specific methodologies
- Specialized approaches for your field
- Technical frameworks relevant to your domain
- Best practices for your area of expertise

**Example documents:**
- healthcare-compliance-guide.pdf
- financial-analysis-framework.docx
- engineering-standards.pdf

### Language Guidelines

**Description:** "Writing style and communication preferences"

Map documents that define:
- Brand voice and tone
- Writing style preferences
- Communication standards
- Terminology and vocabulary

**Example documents:**
- brand-style-guide.pdf
- communication-guidelines.docx
- terminology-glossary.pdf

### Team Capability Profiles

**Description:** "Team member skills and growth areas"

Map documents that describe:
- Team structure and roles
- Individual capabilities
- Growth objectives
- Skills matrix

**Example documents:**
- team-capabilities-matrix.pdf
- role-descriptions.docx
- development-plans.pdf

### Gold Standard Examples

**Description:** "Example documents to emulate"

Map documents that serve as examples:
- Well-written reports or documents
- Model outputs for Thesis to reference
- Templates showing desired format
- Examples of excellent work

**Example documents:**
- sample-executive-report.pdf
- model-analysis-document.docx
- template-presentation.pdf

## Mapping Documents to Slots

### Viewing Currently Mapped Documents

Each template slot shows:
- **Currently Mapped:** section with list of assigned documents
- Or empty if no documents are mapped

### Selecting Documents

Below each slot, all available documents display in a grid:

1. Find the document you want to map
2. Click the checkbox next to the document name
3. Selected documents show with a purple highlight
4. The count updates: "X document(s) selected"

### Multi-Select

You can select multiple documents for each slot:
- Click multiple document checkboxes
- All selected documents will be referenced in that category
- Order may be determined by selection or display order

### Deselecting Documents

To remove a document from a slot:
1. Click the checkbox again to deselect
2. The document highlight removes
3. Count updates accordingly

## Saving Your Mappings

### When You Have Changes

The footer shows: "You have unsaved changes" in amber

### Saving Changes

1. Review your selections for each slot
2. Click **Save Mappings**
3. Wait for confirmation
4. Message appears: "Document mappings saved successfully!"
5. Footer changes to: "All changes saved"

### Canceling Changes

To abandon changes without saving:
- Click **Cancel** in the footer
- Or navigate away from the page

## Regenerating System Instructions

After saving mappings, regenerate instructions to apply changes:

1. Click **Regenerate Instructions**
2. Wait for processing (button shows "Regenerating...")
3. Success message: "System instructions regenerated successfully!"

### When to Regenerate

Regenerate instructions:
- After adding or changing document mappings
- When documents have been updated with new content
- When you want AI behavior to reflect current mappings

## How Mappings Affect Thesis

### Before Mapping

Without document mappings, Thesis uses generic system instructions without specific document references.

### After Mapping

With documents mapped, Thesis's instructions include explicit references:
- "Follow the framework in leadership-guide.pdf"
- "Use the terminology defined in brand-style-guide.docx"
- "Reference team-capabilities-matrix.pdf for role information"

### Response Quality

Proper mapping improves:
- Relevance of responses to your organization
- Consistency with your methodologies
- Alignment with your communication style
- Accuracy of domain-specific guidance

## Best Practices

### Selecting Documents

1. Choose documents that are:
   - Well-written and accurate
   - Relevant to the template slot purpose
   - Current and up-to-date
   - Comprehensive but focused

2. Avoid documents that are:
   - Outdated or deprecated
   - Too general or vague
   - Contradictory to other mapped documents
   - Extremely long (focus on key documents)

### Slot Strategy

**Project Management Models:**
- Start with 1-2 core frameworks
- Add supplementary methods as needed

**Domain-Specific Models:**
- Include your most important industry standards
- Add specialized guides for complex areas

**Language Guidelines:**
- Include your primary style guide
- Add any specialized vocabulary documents

**Team Capability Profiles:**
- Keep current with team changes
- Include growth and development focus

**Gold Standard Examples:**
- Choose your best work as examples
- Include variety of document types

### Regular Maintenance

1. Review mappings quarterly
2. Remove outdated documents
3. Add new relevant content
4. Regenerate instructions after significant changes

## The How This Works Info Box

The blue info box explains:

"Select which uploaded documents the AI should reference for each category below. When you save and regenerate, the AI's instructions will be updated to reference these documents by name (e.g., 'Follow the framework in leadership-guide.pdf')."

## Troubleshooting

### No Documents Available

If a slot shows "No processed documents available":
1. Upload documents first
2. Wait for processing to complete
3. Return to mapping page
4. Click **Upload documents →** link if shown

### Changes Not Taking Effect

If Thesis doesn't seem to follow mapped documents:
1. Verify documents are saved (**All changes saved**)
2. Click **Regenerate Instructions**
3. Wait for confirmation
4. Test with a new conversation

### Document Not Showing

If an uploaded document doesn't appear in the selection grid:
1. Check document processing status in **Dashboard** → **Documents**
2. Verify document is **Processed** status
3. Ensure document belongs to correct client

## Common Tasks

### Setting Up Initial Mappings

1. Access core documents page via user **View Details** → **Manage Core Documents**
2. For each template slot, select relevant documents
3. Click **Save Mappings**
4. Click **Regenerate Instructions**

### Updating After New Document Upload

1. Upload new document through normal process
2. Wait for **Processed** status
3. Navigate to core documents page
4. Add new document to appropriate slot
5. **Save Mappings** → **Regenerate Instructions**

### Removing a Document Reference

1. Open core documents page
2. Find the document in the appropriate slot
3. Click checkbox to deselect
4. **Save Mappings** → **Regenerate Instructions**
