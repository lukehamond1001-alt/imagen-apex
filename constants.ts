
export const APP_NAME = "Imagen Apex";
export const API_VERSION = "v1.3.1";

// Backend endpoint URL for SAM 3D inference server
// Configure this in the Settings modal at runtime, or set DEFAULT_VERTEX_ENDPOINT_URL env var
export const VERTEX_ENDPOINT_URL = import.meta.env.VITE_VERTEX_ENDPOINT_URL || 'http://localhost:8000/predict';

// Fallback model for demo purposes if the backend isn't running
export const DEMO_MODEL_URL = 'https://modelviewer.dev/shared-assets/models/Astronaut.glb';

// Default auth token for backend (set via environment variable)
export const DEFAULT_VERTEX_TOKEN = import.meta.env.VITE_VERTEX_TOKEN || "";