<div align="center">
  <img src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" width="1200" height="475" alt="Imagen Apex Banner" />
  
  # 🎨 Imagen Apex
  
  **AI-Powered Text → 2D Image → 3D Model Pipeline**
  
  [![React](https://img.shields.io/badge/React-19.x-61DAFB?logo=react)](https://react.dev/)
  [![Vite](https://img.shields.io/badge/Vite-6.x-646CFF?logo=vite)](https://vitejs.dev/)
  [![Three.js](https://img.shields.io/badge/Three.js-0.182-black?logo=three.js)](https://threejs.org/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
</div>

---

## ✨ What is Imagen Apex?

Imagen Apex is a full-stack AI pipeline that transforms **text descriptions** into **3D point cloud models** in two steps:

1. **Text → 2D Image**: Uses Google's Gemini 3 Pro to generate high-quality concept art from your prompt
2. **2D → 3D Model**: Converts the generated image into a 3D point cloud using [SAM 3D](https://github.com/facebookresearch/sam-3d) deployed on GPU infrastructure

## 🖼️ Features

- 🎯 **One-Click Pipeline** — Enter a prompt, get a 3D model
- 🖌️ **Optimized Prompts** — Automatically enhances prompts for better 3D reconstruction
- 📦 **Point Cloud Viewer** — Interactive Three.js viewer with auto-rotation
- 💾 **Download** — Export both 2D images and PLY 3D files
- ⚙️ **Configurable Backend** — Connect to any SAM 3D inference server

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌───────────────┐
│   Frontend  │────▶│  Gemini API      │────▶│  2D Image     │
│   (React)   │     │  (Text→Image)    │     │  (1024x1024)  │
└─────────────┘     └──────────────────┘     └───────────────┘
                                                     │
                                                     ▼
┌─────────────┐     ┌──────────────────┐     ┌───────────────┐
│   3D Model  │◀────│  SAM 3D Server   │◀────│  Resized to   │
│   (PLY)     │     │  (GPU Backend)   │     │  256x256      │
└─────────────┘     └──────────────────┘     └───────────────┘
```

## 🚀 Quick Start

### Prerequisites

- [Node.js](https://nodejs.org/) 18+ 
- A [Gemini API key](https://aistudio.google.com/apikey)
- (Optional) SAM 3D backend server for 3D conversion

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/imagen-apex.git
cd imagen-apex

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local and add your GEMINI_API_KEY

# Start the development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to use the app.

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | ✅ | Your Google Gemini API key |
| `VITE_VERTEX_ENDPOINT_URL` | ❌ | SAM 3D backend URL (can configure in UI) |
| `VITE_VERTEX_TOKEN` | ❌ | Auth token for SAM 3D backend |

### Backend Configuration

The 3D conversion requires a running SAM 3D inference server. You can:

1. **Configure in Settings** — Click the ⚙️ icon to set the endpoint URL at runtime
2. **Use environment variables** — Set `VITE_VERTEX_ENDPOINT_URL` in `.env.local`

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, TypeScript, Vite |
| **Styling** | Tailwind CSS |
| **3D Rendering** | Three.js, PLYLoader |
| **AI (Image Gen)** | Google Gemini 3 Pro |
| **AI (3D Gen)** | Meta SAM 3D (self-hosted) |
| **Icons** | Lucide React |

## 📁 Project Structure

```
imagen-apex/
├── App.tsx              # Main application component
├── index.html           # HTML template with import maps
├── index.tsx            # React entry point
├── constants.ts         # App configuration
├── types.ts             # TypeScript interfaces
├── vite.config.ts       # Vite configuration
├── components/
│   ├── Button.tsx       # Styled button component
│   ├── PipelineSteps.tsx # Progress indicator
│   ├── PlyViewer.tsx    # Three.js point cloud viewer
│   └── ProgressBar.tsx  # Loading progress bar
└── services/
    ├── geminiService.ts # Gemini API integration
    └── vertexService.ts # SAM 3D backend integration
```

## 🎥 Demo

[![Watch Demo](https://img.shields.io/badge/YouTube-Watch_Demo-red?logo=youtube)](https://youtube.com/your-demo-link)

> *Enter a text prompt → Generate AI concept art → Transform into 3D point cloud*

## 📄 License

MIT License - feel free to use this project for learning and building!

---

<div align="center">
  <strong>Built with ❤️ using React, Gemini AI, and Three.js</strong>
</div>
