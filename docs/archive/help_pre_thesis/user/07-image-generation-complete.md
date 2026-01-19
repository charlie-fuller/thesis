# Complete Image Generation Guide

Everything you need to know about creating training visuals with Thesis, including advanced features and the standalone image generator.

## Two Ways to Generate Images

### 1. In-Chat Generation

Request images naturally during any conversation:

```
"Generate an image of a diverse team collaborating in a modern office"
"Create a visual showing a manager giving feedback"
```

Thesis automatically detects image requests and generates visuals inline.

**Best for:**
- Context-specific images related to your current project
- Iterative refinement with follow-up requests
- Quick visuals during content development

### 2. Standalone Image Generator

Access the dedicated image generation tool:

1. Go to `/generate` or click **Generate** in the navigation
2. Enter your image description
3. Select aspect ratio and quality settings
4. Click **Generate**

**Best for:**
- Batch image creation
- Experimenting with different settings
- Creating images without conversation context

## Aspect Ratio Options

Choose the right format for your use case:

| Ratio | Dimensions | Best For |
|-------|------------|----------|
| **1:1** (Square) | Equal width/height | Social media, icons, badges |
| **16:9** (Landscape) | Wide format | Presentations, slides, banners |
| **9:16** (Portrait) | Tall format | Mobile, posters, vertical displays |
| **4:3** (Standard) | Classic ratio | Documents, traditional screens |

### Specifying Aspect Ratio

**In chat:**
```
"Generate a landscape image of..."
"Create a portrait image showing..."
"Generate a square image for..."
```

**In standalone generator:**
Select from the aspect ratio buttons before generating.

## Quality Settings

The standalone generator offers quality options:

| Setting | Speed | Quality | Best For |
|---------|-------|---------|----------|
| **Fast** | 3-5 seconds | Good | Drafts, brainstorming, quick concepts |
| **Quality** | 8-12 seconds | High | Final deliverables, client presentations |

**When to use Fast:**
- Exploring visual concepts
- Generating multiple variations quickly
- Internal use or rough drafts

**When to use Quality:**
- Client-facing materials
- Print materials
- Final training content

## Prompting for Better Results

### The Anatomy of a Good Prompt

Include these elements for best results:

1. **Subject** - Who or what is in the image
2. **Action** - What they're doing
3. **Setting** - Where it's taking place
4. **Style** - The mood or visual style
5. **Details** - Specific elements to include

**Example:**
```
"A diverse group of healthcare workers (1 male doctor, 2 female nurses, 1 male technician)
collaborating around a patient chart in a bright, modern hospital corridor.
Professional and caring atmosphere with natural lighting."
```

### Diversity and Representation

Thesis defaults to inclusive representation. Be explicit when you have specific requirements:

```
"Generate an image showing a diverse team including:
- Different ages (20s to 60s)
- Multiple ethnicities
- Various body types
- Someone using a wheelchair"
```

### Emotional Tone

Describe the feeling you want to convey:

| Desired Tone | Prompt Language |
|--------------|-----------------|
| Professional | "corporate setting", "formal", "polished" |
| Collaborative | "engaged discussion", "leaning in", "active listening" |
| Innovative | "creative space", "brainstorming", "energetic" |
| Supportive | "mentoring", "empathetic", "warm interaction" |
| Serious | "focused", "concentrated", "thoughtful" |

### Camera Perspective

Specify viewpoint when it matters:

```
"Close-up showing facial expressions..."
"Wide shot showing the full team..."
"Over-the-shoulder view of..."
"Bird's eye view of the workspace..."
```

## Advanced Techniques

### Creating Image Series

For consistent visual sets (e.g., for a course):

1. Describe a consistent style in your first request
2. Reference it in subsequent requests:
   ```
   "Using the same style as the previous image, generate..."
   "Create another scene in this setting..."
   ```

### Iterating on Images

When the first result isn't quite right:

```
"Generate the same scene but with more natural lighting"
"Keep the composition but make the expressions more engaged"
"Same setting, but show them from a different angle"
```

### Creating Variations

Request multiple options:

```
"Generate 3 different variations of a manager coaching an employee"
```

## Using Generated Images

### Downloading Images

1. Click on the generated image to view full size
2. Right-click and select **Save Image As**
3. Choose your save location

Or click the **download** icon below the image.

### Image Storage

- Generated images are stored in your conversation
- They remain accessible as long as the conversation exists
- Images are saved at full resolution

### Using in Training Materials

Generated images work well for:
- **PowerPoint/Keynote** - Drag and drop directly
- **Word/Google Docs** - Insert as image
- **E-learning tools** - Export and upload
- **Handouts** - Print-quality resolution

**Tip:** Add text overlays in your presentation tool rather than requesting text in the image.

## Common Use Cases

### Leadership Development

```
"A senior executive mentoring a mid-level manager in a quiet office corner,
both looking at a tablet, collaborative posture, warm lighting"

"A leader facilitating a strategic planning session with 6 diverse
team members around a whiteboard, engaged and participatory"
```

### Customer Service Training

```
"A customer service representative demonstrating active listening with a
customer at a retail counter, making eye contact, professional and warm"

"A call center employee handling a difficult call, showing calm and
empathetic body language, modern open-plan office background"
```

### Sales Training

```
"A sales professional presenting a solution on a laptop to two clients
in a glass-walled meeting room, confident but approachable"

"A salesperson networking at a business event, engaging in conversation
with a potential client, professional casual dress"
```

### Onboarding & Orientation

```
"A new employee being welcomed by their team in a modern office,
diverse group showing genuine smiles, inclusive atmosphere"

"An HR manager giving an office tour to a group of new hires,
pointing out features of the workspace, friendly and informative"
```

### Compliance & Safety

```
"Workers in a warehouse following proper safety protocols, wearing
PPE, organized and clean environment"

"Office employees reviewing a compliance document together,
focused and attentive expressions"
```

## Troubleshooting

### Image Doesn't Match Vision

**Problem:** The generated image isn't what you imagined.

**Solutions:**
- Add more specific details to your prompt
- Describe what's wrong with the current image
- Break complex scenes into simpler descriptions

### Inconsistent Style Across Images

**Problem:** Images for the same project look different.

**Solutions:**
- Include style keywords in every prompt: "clean, modern, bright lighting"
- Reference the style: "Match the visual style of the previous image"
- Generate all images in one session

### Faces or Details Look Wrong

**Problem:** Faces appear distorted or details are incorrect.

**Solutions:**
- Request a different angle or distance
- Ask for a wider shot if faces are problematic
- Regenerate with slightly different wording

### Generation Failed

**Problem:** The image didn't generate at all.

**Solutions:**
- Check your internet connection
- Try a simpler prompt
- Wait a moment and retry
- Contact support if issues persist

## Limitations

Thesis's image generation cannot:

- Generate **readable text** within images
- Create images of **real, identifiable people**
- Include **copyrighted logos or brands**
- Produce **photo-realistic** images of specific locations
- Generate **complex technical diagrams** (use dedicated tools)
- Create **animated images or videos**

## Best Practices Summary

1. **Be specific** - Details matter for accurate results
2. **Iterate** - First images rarely perfect, refine with follow-ups
3. **Stay consistent** - Use similar style language for image sets
4. **Plan diversity** - Request inclusive representation intentionally
5. **Match context** - Align images with your training content tone
6. **Test early** - Generate images while developing content, not at the end

## Related Guides

- [Image Generation Guide](image-generation.md) - Core image generation concepts
- [Conversations and Chat](06-conversations-and-chat.md) - Using images in conversations
- [Templates and Shortcuts](08-templates-and-shortcuts.md) - Quick image commands
