# Thesis - Frontend

Multi-agent GenAI strategy platform built with Next.js 16, featuring 21 specialized agents, meeting rooms, task management, and stakeholder tracking.

## Tech Stack

- **Framework**: Next.js 16.0.1 (App Router with Turbopack)
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4 with class-based dark mode
- **UI Components**: React 19
- **Authentication**: Supabase Auth
- **State Management**: React Context API
- **API Client**: Custom fetch wrapper with JWT handling

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Access to Supabase project
- Backend API running on Railway (or locally)

### Installation

```bash
npm install
```

### Environment Variables

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=https://thesis-production.up.railway.app
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

### Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to see the application.

### Build for Production

```bash
npm run build
npm start
```

## Project Structure

```
/app
  /admin              # Admin dashboard and management
    /agents           # Agent instruction management
    /users            # User management (admin only)
    /theme            # Theme settings (admin only)
  /auth               # Authentication pages
  /chat               # Main chat interface with agent selection
  /meeting-room       # Multi-agent meeting rooms
  /tasks              # Kanban task management
  /opportunities      # AI opportunity pipeline
  /meeting-prep       # Stakeholder briefing pages
  /intelligence       # Analytics and engagement trends
  /kb                 # Knowledge Base (documents + conversations)
  /disco              # DISCo product discovery pipeline
  /strategy           # Strategic alignment (company objectives, KPIs)
  /profile            # User profile
  globals.css         # Global styles with theme support
  layout.tsx          # Root layout with providers

/components
  /meeting-room       # Meeting room components
  /tasks              # Kanban board components
  /kb                 # Knowledge Base components
  /opportunities      # Opportunities components
  /disco              # DISCo pipeline components (7 files)
  ChatInterface.tsx   # Main chat with agent selection
  AgentSelector.tsx   # Agent dropdown selector
  AgentIcon.tsx       # Agent icons and colors (single source of truth)
  UserMenu.tsx        # Hamburger menu with profile, theme, users links

/contexts
  /AuthContext.tsx    # Authentication state
  /ThemeContext.tsx   # Dark mode theme
  /HelpChatContext.tsx # Help system state

/lib
  /api.ts             # API client with JWT handling
```

## Features

### Multi-Agent System
- 21 specialized agents for enterprise GenAI strategy
- Agent selector UI for choosing up to 3 agents
- @mention syntax for inline agent invocation
- Agent badges on responses showing attribution
- Coordinator auto-routes to appropriate specialists

### Meeting Rooms
- Multi-agent collaboration spaces
- Autonomous discussion mode (agents debate topics)
- Facilitator orchestration and Reporter synthesis
- Real-time streaming responses
- Speaking order display during autonomous mode

### Task Management
- Kanban board with drag-and-drop
- Priority levels (P1-P4) with color coding
- Assignee tracking with stakeholder integration
- Task extraction from meeting transcripts

### Opportunities Pipeline
- Tier-based AI opportunity scoring (1-4)
- 4-dimension scoring criteria
- Department and stakeholder ownership
- Status tracking through lifecycle

### Knowledge Base
- Document upload with auto-classification
- Agent-filtered RAG retrieval
- Google Drive and Notion integration
- Local vault sync

### DISCo Pipeline
- 8 specialized agents for product discovery
- Workflow: Triage → Discovery Planner → Coverage Tracker → Insight Extractor → Consolidator → Strategist → PRD Generator → Tech Evaluation
- Initiative management with document upload
- Agent outputs with versioning and human-in-the-loop guidance
- Initiative bundles and PRD generation

### Stakeholder Intelligence
- CRM-style tracking with engagement analytics
- Meeting prep pages with briefings
- Engagement trends visualization
- Sentiment and alignment tracking

### Authentication & Theme
- JWT-based authentication via Supabase
- Class-based dark mode with Tailwind CSS
- WCAG AA accessible color contrasts
- Theme persistence via localStorage

## Styling System

### WCAG AA Accessibility

All colors meet WCAG AA standards with proper contrast ratios:

- **Normal text**: 4.5:1 minimum
- **Large text**: 3:1 minimum
- **Icons & stats**: 8:1+ (AAA level)

### Global CSS Classes

See [STYLING-GUIDE.md](STYLING-GUIDE.md) for comprehensive documentation.

**Component Classes**:
- `.input-field` - Form inputs with dark mode
- `.btn-primary` - Primary action buttons
- `.btn-secondary` - Secondary buttons
- `.card` - Container cards
- `.page-bg` - Page backgrounds

**Utility Classes**:
- `.text-accent` - Accent color text (blue-600/400)
- `.icon-color` - SVG icons with proper contrast
- `.stat-number` - Large statistics numbers
- `.heading-1/2/3` - Semantic headings

**Example Usage**:
```tsx
<input className="input-field" placeholder="Search..." />
<button className="btn-primary">Save</button>
<div className="card p-6">
  <h2 className="heading-2">Title</h2>
  <div className="stat-number">42</div>
</div>
```

## API Integration

### Custom Fetch Wrapper

All API calls use `/lib/api.ts` which handles:
- JWT token injection from cookies
- Automatic error handling
- Response parsing
- Network error recovery

**Usage**:
```typescript
import { apiGet, apiPost, apiPut, apiDelete } from '@/lib/api';

// GET request
const response = await apiGet('/api/clients');
const data = await response.json();

// POST request with body
await apiPost('/api/clients', { name: 'Acme Corp', email: 'admin@acme.com' });

// PUT request
await apiPut(`/api/users/${userId}`, { role: 'client_admin' });

// DELETE request
await apiDelete(`/api/conversations/${id}`);
```

## Dark Mode Implementation

### Theme Context

Dark mode is managed via `ThemeContext`:

```typescript
import { useTheme } from '@/contexts/ThemeContext';

function MyComponent() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button onClick={toggleTheme}>
      {theme === 'dark' ? 'Light' : 'Dark'}
    </button>
  );
}
```

### Tailwind Configuration

```javascript
// tailwind.config.js
export default {
  darkMode: 'class', // Class-based dark mode
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  // ...
}
```

### Dark Mode Classes

Use Tailwind's `dark:` prefix for dark mode variants:

```tsx
<div className="bg-white dark:bg-gray-800 text-[#1d1d22] dark:text-white">
  Content adapts to theme
</div>
```

**Force Important Styles** (when needed):
```tsx
<input className="dark:!text-white" /> {/* ! prefix adds !important */}
```

## Deployment

### Vercel (Frontend)

Automatic deployment from `main` branch:

1. Push to GitHub
2. Vercel auto-deploys from main branch
3. Environment variables configured in Vercel dashboard

**Production URL**: https://thesis-woad.vercel.app

### Environment Setup

Required environment variables in Vercel:
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

## Common Issues & Solutions

### Issue: Dark Mode Not Working
**Solution**: Ensure `darkMode: 'class'` in `tailwind.config.js` and `.dark` class is toggled on `<html>` element

### Issue: Text Invisible in Dark Mode
**Solution**: Use `dark:!text-white` syntax for inputs to force white text with `!important`

### Issue: Build Error - Unknown Utility Class
**Solution**: Tailwind v4 doesn't support custom colors in `@apply`. Use standard color names like `blue-600` instead of `primary-600`

### Issue: API Returns 401 Unauthorized
**Solution**: Check JWT token in cookies. May need to re-authenticate if token expired.

### Issue: Browser Shows Old Styles
**Solution**: Hard refresh with Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows) to clear cache

## Development Workflow

1. **Make Changes**: Edit files in `/app` or `/components`
2. **Test Locally**: Dev server hot-reloads automatically
3. **Check Dark Mode**: Toggle theme to verify both modes
4. **Commit**: Push to GitHub
5. **Deploy**: Vercel auto-deploys from main branch
6. **Verify**: Check production URL after deployment

## Testing

### Manual Testing Checklist

- [ ] Light mode displays correctly
- [ ] Dark mode displays correctly
- [ ] All text is readable (sufficient contrast)
- [ ] Forms submit successfully
- [ ] Navigation works across all routes
- [ ] Protected routes redirect when unauthenticated
- [ ] API calls return expected data
- [ ] Theme persists after page refresh

## Performance

- **Turbopack**: Fast development builds
- **Code Splitting**: Automatic route-based splitting
- **Image Optimization**: Next.js Image component
- **Font Optimization**: Geist font with next/font

## Accessibility

- WCAG AA compliant color contrasts
- Semantic HTML structure
- Keyboard navigation support
- Screen reader friendly
- Dark mode for reduced eye strain

## Contributing

1. Create feature branch
2. Make changes
3. Test thoroughly (light + dark mode)
4. Commit with descriptive messages
5. Push and create pull request

## Learn More

- [Next.js Documentation](https://nextjs.org/docs)
- [Tailwind CSS v4](https://tailwindcss.com/docs/v4-beta)
- [Supabase Docs](https://supabase.com/docs)
- [STYLING-GUIDE.md](STYLING-GUIDE.md) - Comprehensive styling reference

## Support

For issues or questions:
1. Review [CLAUDE.md](../CLAUDE.md) for development conventions
2. Check [STYLING-GUIDE.md](STYLING-GUIDE.md) for styling patterns
3. Check Supabase dashboard for auth/database issues
4. Review Railway logs for backend API issues
5. See [docs/AGENT_GUARDRAILS.md](../docs/AGENT_GUARDRAILS.md) for agent behavior rules

---

**Last Updated**: January 2026
**Version**: 2.0 (Multi-Agent Platform)
**Status**: Production


