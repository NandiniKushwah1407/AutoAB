# AutoAB - Simple React Frontend

Clean React dashboard for AutoAB A/B testing platform using Create React App (no Vite/Tailwind).

## Features

- ✅ List all experiments with status badges
- ✅ Create new experiments with comprehensive configuration
- ✅ Detailed experiment view with real-time updates
- ✅ Statistical analysis results display
- ✅ LLM diff analysis viewer
- ✅ AI-generated report display
- ✅ Start/stop/delete experiment controls

## Quick Start

### Install Dependencies

```bash
npm install
```

### Start Development Server

```bash
npm start
```

Runs on http://localhost:3000

### Build for Production

```bash
npm run build
```

## Project Structure

```
frontend/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── index.js            # Entry point
│   ├── App.js              # Main app with routing
│   ├── index.css           # Global styles
│   ├── api.js              # API client
│   └── pages/
│       ├── ExperimentsList.js    # Grid view of experiments
│       ├── CreateExperiment.js   # Create form
│       └── ExperimentDetail.js   # Detailed view with tabs
└── package.json
```

## API Integration

The app proxies API requests to `http://localhost:8000` (configured in package.json).

Make sure your backend is running:

```bash
cd ../
docker compose up -d
```

## Usage

### 1. List Experiments
- View all experiments in a grid layout
- See status, URLs, and metrics at a glance
- Quick actions: View, Start, Stop, Delete

### 2. Create Experiment
- Fill in experiment details
- Configure URLs for control (A) and treatment (B)
- Set statistical parameters (alpha, power, MDE)
- Choose primary metric and duration
- LLM automatically analyzes differences

### 3. View Details
- **Overview Tab**: Key metrics with comparisons
- **Results Tab**: Statistical test results and recommendation
- **Diff Tab**: LLM-detected changes and hypotheses
- **Report Tab**: AI-generated summary with verdict

### 4. Control Experiments
- Start experiments when ready
- Stop manually or let them complete
- Real-time updates every 30 seconds for running experiments
- Generate AI reports after stopping

## Styling

Uses plain CSS with a clean, modern design system:
- Responsive grid layouts
- Card-based UI
- Color-coded status badges
- Hover effects and transitions
- Mobile-friendly

## Dependencies

- **react**: ^18.2.0 - UI library
- **react-dom**: ^18.2.0 - React rendering
- **react-scripts**: 5.0.1 - Build tooling (Create React App)
- **react-router-dom**: ^6.20.0 - Client-side routing
- **axios**: ^1.6.0 - HTTP client

## Environment Variables

Create `.env` file (optional):

```
REACT_APP_API_URL=http://localhost:8000
```

Default: http://localhost:8000

## Browser Support

- Chrome/Edge: Last 2 versions
- Firefox: Last 2 versions
- Safari: Last 2 versions

## Development Tips

- Component files use `.js` extension
- Styles are in vanilla CSS
- API proxy configured in package.json
- Auto-refresh enabled for running experiments
- Error boundaries for graceful error handling

## Troubleshooting

### Port 3000 already in use
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Mac/Linux
lsof -ti:3000 | xargs kill
```

### API connection issues
- Ensure backend is running on port 8000
- Check Docker containers: `docker ps`
- Verify proxy setting in package.json

### Build errors
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```
