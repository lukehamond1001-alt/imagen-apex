export interface GeneratedImage {
  base64: string;
  mimeType: string;
}

export enum PipelineStage {
  IDLE = 'IDLE',
  GENERATING_IMAGE = 'GENERATING_IMAGE',
  IMAGE_READY = 'IMAGE_READY',
  CONVERTING_3D = 'CONVERTING_3D',
  COMPLETE = 'COMPLETE',
  ERROR = 'ERROR'
}

export interface Model3DResponse {
  model_3d_base64: string; // The backend returns this key
}

// Extend Window interface for AI Studio
declare global {
  interface AIStudio {
    hasSelectedApiKey: () => Promise<boolean>;
    openSelectKey: () => Promise<void>;
  }

  interface Window {
    aistudio?: AIStudio;
  }
}