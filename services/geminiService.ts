
import { GoogleGenAI } from "@google/genai";
import { GeneratedImage } from "../types";

/**
 * Generates an image using Gemini 3 Pro (Nano Banana Pro)
 * @param prompt User description
 * @returns Promise<GeneratedImage>
 */
export const generateImageFromText = async (prompt: string): Promise<GeneratedImage> => {
  // Initialize client with process.env.API_KEY directly inside the function.
  // This ensures the client uses the most up-to-date key selected by the user.
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

  try {
    // SAM 3D Optimization Strategy (L4 GPU / 256x256 Limit):
    // To get the best 3D results, we need maximum contrast and zero background distraction.
    // "White background": Critical. Stops SAM 3D from turning walls/trees into 3D shapes.
    // "Isometric/3/4 view": Critical. Provides depth information for single-view reconstruction.
    // "Centered": Ensures the object isn't cut off.
    // "Full shot": Prevents zooming in too close.
    // "Studio lighting": Ensures good 3D definition.
    const optimizedPrompt = `${prompt}, isometric view, 3/4 angle showing all dimensions and depth, full body, centered, solid white background, studio lighting, high contrast, minimal, 3d render style. No complex background, no text, no watermarks, no cropping.`;

    // Using 'Nano Banana Pro': gemini-3-pro-image-preview
    // This model supports higher resolution and better adherence to prompts.
    const response = await ai.models.generateContent({
      model: 'gemini-3-pro-image-preview',
      contents: {
        parts: [
          {
            text: optimizedPrompt,
          },
        ],
      },
      config: {
        imageConfig: {
          aspectRatio: "1:1", // Critical: Forces square output so downscaling doesn't distort geometry.
          imageSize: "1K" // Supported in Pro models for better texture details
        }
      },
    });

    // Parse response
    const candidates = response.candidates;
    if (!candidates || candidates.length === 0) {
      throw new Error("No candidates returned from Gemini.");
    }

    // Iterate through parts to find the inline image data
    for (const part of candidates[0].content.parts) {
      if (part.inlineData) {
        return {
          base64: part.inlineData.data,
          mimeType: part.inlineData.mimeType || 'image/png',
        };
      }
    }

    throw new Error("No image data found in the response.");

  } catch (error) {
    console.error("Gemini Image Generation Error:", error);
    throw error;
  }
};
