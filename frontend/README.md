# Agentic AI Project Management Assistant - Frontend

A modern React + Vite frontend for the AI-powered project management system.

## Features

- **React 18** with modern hooks and patterns
- **Vite** for fast development and building
- **Tailwind CSS** for utility-first styling
- **React Router** for client-side routing
- **React Query** for server state management
- **Chart.js** for data visualization
- **Real-time updates** with WebSocket integration
- **Responsive design** for mobile and desktop

## Quick Start

### Prerequisites

- Node.js 18 or higher
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

## Configuration

### Environment Variables

Create a `.env.local` file for local development:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_GITHUB_CLIENT_ID=your-github-client-id
```

## Features

### Dashboard
- Project overview and statistics
- Task completion metrics
- AI-powered insights and suggestions
- Recent activity feed

### Project Management
- Create and manage projects
- Team collaboration features
- Project analytics and reporting
- Deadline tracking

### Task Management
- Drag-and-drop task boards
- Task assignment and prioritization
- Progress tracking
- Comment system

### AI Assistant
- Natural language command processing
- Intelligent task suggestions
- Risk analysis and alerts
- Automated priority recommendations

### Analytics
- Productivity metrics
- Project performance reports
- Team collaboration insights
- Exportable reports

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **React Router** - Routing
- **React Query** - Data fetching
- **Axios** - HTTP client
- **Chart.js** - Charts
- **React Beautiful DnD** - Drag and drop
- **React Hot Toast** - Notifications
- **Lucide React** - Icons

## Project Structure

```
frontend/
├── public/
├── src/
│   ├── components/         # Reusable components
│   │   ├── Dashboard/      # Dashboard components
│   │   ├── Tasks/          # Task management
│   │   ├── AI/             # AI chat interface
│   │   ├── Reports/        # Analytics components
│   │   ├── Layout/         # Layout components
│   │   └── UI/             # UI primitives
│   ├── pages/              # Page components
│   │   ├── Dashboard.jsx
│   │   ├── Projects.jsx
│   │   ├── Tasks.jsx
│   │   └── Analytics.jsx
│   ├── hooks/              # Custom hooks
│   ├── services/           # API services
│   │   └── api.js
│   ├── store/              # State management
│   │   └── AuthContext.jsx
│   ├── utils/              # Utilities
│   ├── App.jsx             # Main app component
│   ├── main.jsx            # Entry point
│   └── index.css           # Global styles
├── package.json
├── vite.config.js
├── tailwind.config.js
└── README.md
```

## Development

### Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

### Code Style

- Use functional components with hooks
- Follow React best practices
- Use Tailwind CSS for styling
- Implement responsive design patterns

## Deployment

### Netlify (Recommended)

1. Connect your GitHub repository to Netlify
2. Set build command: `npm run build`
3. Set publish directory: `dist`
4. Configure environment variables

### Vercel

```bash
npm install -g vercel
vercel
```

### Static Hosting

```bash
npm run build
# Upload `dist` folder to your hosting provider
```

## Contributing

1. Follow the existing code style
2. Write meaningful commit messages
3. Test your changes thoroughly
4. Update documentation as needed

## License

MIT License