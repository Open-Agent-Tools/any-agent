# Any Agent React UI

A modern React TypeScript Material-UI single page application for the Any Agent framework, replacing the current HTML template system with a fully interactive and responsive interface.

## Features

- **React 18** with TypeScript for type safety
- **Material-UI (MUI)** components with custom theme matching existing style guide
- **Real-time chat interface** with A2A protocol integration
- **Responsive design** that works across mobile, tablet, and desktop
- **Session management** with unique session IDs and cleanup
- **Rich text formatting** for chat messages (markdown-style lists, code blocks, bold/italic)
- **Connection status indicators** (connecting/connected/error)
- **Agent metadata display** and API documentation
- **Navigation menu** with hamburger menu design
- **Accessibility compliant** with WCAG 2.1 AA standards

## Architecture

### Technology Stack
- React 18.2+ with TypeScript
- Material-UI 5.14+ for UI components  
- React Router 6.15+ for client-side routing
- Vite 4.4+ for build tooling and development server
- ESLint + TypeScript ESLint for code quality

### Project Structure
```
src/
├── components/          # Reusable UI components
│   ├── Header.tsx       # Fixed header with branding and navigation
│   ├── Navigation.tsx   # Slide-out navigation menu
│   ├── Footer.tsx       # Fixed footer with agent info
│   └── LoadingIndicator.tsx
├── pages/               # Main page components
│   ├── ChatPage.tsx     # Real-time chat interface
│   └── DescriptionPage.tsx # Agent documentation
├── theme/               # Material-UI theme configuration
│   └── index.ts         # Custom theme matching existing colors
├── types/               # TypeScript type definitions
│   └── index.ts         # All shared interfaces and types
├── utils/               # Utility functions
│   ├── api.ts           # API client functions
│   └── messageFormatter.ts # Message formatting utilities
├── App.tsx              # Main app component with routing
└── main.tsx             # Application entry point
```

## API Integration

The application integrates with the following Any Agent endpoints:

- `/.well-known/agent-card.json` - Agent metadata
- `/chat/create-session` - Create new chat session
- `/chat/send-message` - Send message to agent
- `/chat/cleanup-session` - Clean up session
- `/health` - Health check endpoint

## Development

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation
```bash
cd src/any_agent/ui
npm install
```

### Development Server
```bash
npm run dev
```
Starts development server at http://localhost:3000 with proxy to backend at http://localhost:8080

### Building for Production
```bash
npm run build
```
Builds the app for production to the `dist/` folder.

### Type Checking
```bash
npm run type-check
```

### Linting
```bash
npm run lint
```

## Theme Configuration

The Material-UI theme is configured to match the existing Any Agent color scheme:

### Primary Colors
- Primary Blue: `#1f4788` (main navigation, buttons)
- Primary Blue Light: `#3f67a8` (hover states)
- Primary Blue Dark: `#0f2748` (header background)
- Primary Green: `#1f7a4f` (secondary actions)

### Neutral Colors
- White: `#ffffff` (backgrounds)
- Light Grey: `#f8f9fa` (table headers, cards)
- Medium Grey: `#dee2e6` (borders, dividers)
- Dark Grey: `#6c757d` (secondary text)
- Darkest: `#212529` (primary text)

### Typography
- Primary Font: 'Roboto', sans-serif
- Monospace Font: 'Roboto Mono', monospace (code, session IDs)

## Functionality Preservation

All functionality from the original HTML templates is preserved:

### Chat Interface
- ✅ Real-time chat with A2A protocol
- ✅ Session management and cleanup
- ✅ Connection status indicators
- ✅ Message formatting (markdown-style)
- ✅ "New Chat" functionality
- ✅ Enter key to send messages
- ✅ Auto-scroll to latest messages
- ✅ Responsive design (66.67% desktop, 95% mobile)

### Navigation
- ✅ Fixed header with branding
- ✅ Hamburger menu with slide-out navigation
- ✅ Links to health, description, agent card endpoints
- ✅ Mobile-responsive menu

### Agent Description
- ✅ Agent metadata display (framework, model, port, status)
- ✅ Complete API endpoint documentation table
- ✅ Usage examples with curl commands
- ✅ Responsive card-based layout

### Footer
- ✅ Fixed footer with agent framework info
- ✅ Protocol compatibility indicators

## Responsive Design

The application uses Material-UI's responsive breakpoints:

- **Mobile** (xs): Full width chat (95%), compact header
- **Tablet** (md): 80% width chat container
- **Desktop** (lg+): 66.67% width chat container, full navigation

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Accessibility

- WCAG 2.1 AA compliant color contrast
- Proper ARIA labels and semantic HTML
- Keyboard navigation support
- Screen reader compatible
- Color-blind friendly palette

## Integration with Any Agent Framework

This React application replaces the Python HTML template generation in:
- `clean_landing_page.py` - Chat interface (root page)
- `landing_page.py` - Description page

The build output in `dist/` can be served by the Any Agent framework's web server, maintaining the same URL structure and API endpoints.