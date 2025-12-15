# Imagen Apex Frontend

React-based web interface for the Imagen Apex pipeline.

## Quick Start

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local and add your GEMINI_API_KEY

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to use the app.

## Tech Stack

- **React 19** + TypeScript
- **Vite** for development/build
- **Three.js** for 3D point cloud rendering
- **Tailwind CSS** for styling
- **Google Gemini** for image generation
- **SAM 3D** backend for 2D→3D conversion

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ | Google Gemini API key |
| `VITE_VERTEX_ENDPOINT_URL` | ❌ | SAM 3D backend URL |
| `VITE_VERTEX_TOKEN` | ❌ | Auth token for backend |

## Build

```bash
npm run build
npm run preview
```
