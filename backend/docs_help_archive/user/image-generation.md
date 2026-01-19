# Image Generation Guide

Thesis can generate high-quality training visuals in 3-5 seconds using Google's Gemini 2.5 Flash Image model.

## What You Can Generate

### Scenario Backgrounds
- **Office settings** - Modern workspaces, meeting rooms, collaborative areas
- **Retail environments** - Stores, customer service counters, stock rooms
- **Healthcare** - Hospitals, clinics, patient care settings
- **Manufacturing** - Factory floors, quality control, safety scenarios
- **Remote work** - Home offices, virtual meetings, distributed teams

### Concept Visualizations
- **Leadership** - Coaching, feedback, strategic thinking
- **Teamwork** - Collaboration, communication, conflict resolution
- **Growth mindset** - Learning, development, resilience
- **Customer service** - Empathy, problem-solving, professionalism
- **Diversity & inclusion** - Representation across age, ethnicity, ability

### Training Materials
- **Job aids** - Step-by-step process diagrams
- **Decision trees** - Troubleshooting flowcharts
- **Checklists** - Quality standards, safety protocols
- **Presentation graphics** - Engaging visuals for slides
- **Scenario cards** - Realistic workplace situations

## How to Request Images

### Natural Language Requests

Thesis automatically detects when you want an image. Just describe what you need:

**Examples:**
```
"Generate an image of a diverse team brainstorming in a modern office"
"Show me a manager giving constructive feedback to an employee"
"Create an image of a customer service representative on a phone call"
"Generate a landscape image of a peaceful workspace for mindfulness training"
```

### Using the /image Command

For quick generation, use the `/image` command:

```
/image diverse team collaborating
/image manager coaching employee
/image customer service scenario
```

## Aspect Ratios

Choose the right aspect ratio for your use case:

- **Square (1:1)** - Social media, profile images, icons
- **Landscape (16:9)** - Presentations, slides, wide screens
- **Portrait (9:16)** - Mobile screens, posters, vertical displays

Specify in your request:
```
"Generate a landscape image of..."
"Create a portrait image of..."
```

## Best Practices

### Be Specific
**Good:** "Generate an image of a female manager in her 40s giving positive feedback to a young male employee in a modern office with natural lighting"

**Less effective:** "Show me a manager talking to someone"

### Include Diversity
Thesis defaults to inclusive representation, but you can be explicit:
```
"Generate an image showing a diverse team (different ages, ethnicities, abilities) collaborating"
```

### Set the Mood
Describe the atmosphere:
- "Professional and corporate"
- "Casual and collaborative"
- "Serious and focused"
- "Energetic and creative"

### Specify Details
- **Setting:** "modern office", "retail store", "hospital ward"
- **Lighting:** "natural light", "bright and airy", "warm tones"
- **Activity:** "brainstorming", "presenting", "listening", "problem-solving"
- **Emotions:** "engaged", "thoughtful", "confident", "empathetic"

## Common Use Cases

### Leadership Training
```
"Generate an image of a senior leader mentoring a junior employee in a quiet office space"
"Show a manager facilitating a team meeting with diverse participants engaged"
```

### Customer Service Training
```
"Create an image of a retail employee helping an elderly customer with a product"
"Generate an image of a call center representative using active listening skills"
```

### Sales Training
```
"Show a sales professional presenting a solution to a client in a meeting room"
"Generate an image of a salesperson building rapport with a potential customer"
```

### Compliance & Safety Training
```
"Create an image of workers following proper safety protocols in a factory"
"Show employees reviewing compliance documentation together"
```

## Multiple Images in One Conversation

You can generate multiple images in the same conversation:

```
User: "I need three images for my customer service training"

Thesis: "I'll help you create those. What scenarios do you need?"

User: "First, a rep greeting a customer. Second, handling a complaint. Third, closing a successful interaction"

Thesis: [Generates three separate images in sequence]
```

## Limitations

- **Text in images** - Currently cannot generate readable text within images
- **Specific people** - Cannot generate images of real, named individuals
- **Logos/brands** - Cannot include copyrighted logos or brand marks
- **Highly technical diagrams** - Better to use dedicated diagramming tools for complex technical illustrations

## Tips for Best Results

1. **Start broad, then refine** - Generate an initial image, then request adjustments
2. **Use consistent style** - If creating multiple images for one course, describe similar settings/style
3. **Request variations** - "Generate three variations of this scene with different perspectives"
4. **Combine with text** - Use generated images as backgrounds and add text overlays in your presentation tool
5. **Test before delivery** - Generate images early so you have time to iterate

## Troubleshooting

### Image doesn't match my vision
Be more specific in your next request:
```
"Generate the same scene but with more natural lighting and showing the full room"
```

### Need a different perspective
Request a specific viewpoint:
```
"Generate this from a different angle, showing the interaction from the side"
```

### Want to adjust composition
Be explicit about what you want:
```
"Generate this image again but with the people closer together and the background less prominent"
```

## Getting Help

If you're not sure how to describe what you need:
- Share a reference description of similar imagery
- Describe the training objective and let Thesis suggest visual concepts
- Ask: "What kind of image would work well for teaching [concept]?"

Need assistance? Ask Thesis: "How should I describe the image I need?" or "What makes a good training visual?"
