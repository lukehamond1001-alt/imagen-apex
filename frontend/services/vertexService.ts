
import { DEFAULT_VERTEX_TOKEN, VERTEX_ENDPOINT_URL } from "../constants";

/**
 * Resizes a base64 image string to specific dimensions.
 * Returns raw base64 string (no data URI prefix).
 */
function resizeImage(base64Str: string, width: number, height: number): Promise<string> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    // Handle cases where input might already have prefix or not
    const src = base64Str.startsWith('data:image') 
      ? base64Str 
      : `data:image/png;base64,${base64Str}`;
    
    img.onload = () => {
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      if (ctx) {
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(img, 0, 0, width, height);
        const dataUrl = canvas.toDataURL('image/png');
        resolve(dataUrl.split(',')[1]);
      } else {
        reject(new Error("Failed to create canvas context"));
      }
    };
    img.onerror = (e) => reject(e);
    img.src = src;
  });
}

/**
 * Generates a white mask (raw base64) of specific dimensions.
 * This tells the SAM 3D model that the entire image is the subject.
 */
function createWhiteMask(width: number, height: number): string {
  // Create a canvas element
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  
  // Fill it with white
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, width, height);
  }
  
  // Get Data URL and strip the "data:image/png;base64," prefix to get raw base64
  const dataUrl = canvas.toDataURL('image/png');
  return dataUrl.split(',')[1];
}

export async function generate3DFromImage(imageBase64: string): Promise<Blob> {
  const controller = new AbortController();
  // Backend now features aggressive GPU memory cleanup
  // Timeout set to 5 minutes to accommodate deep inference.
  const timeout = setTimeout(() => controller.abort(), 300000);

  try {
    // Optimization: Resize image to 256x256 on client side.
    // This is a confirmed stable resolution for the L4 GPU (22GB VRAM).
    console.log("[SAM 3D] Pre-processing: Resizing to 256x256 for L4 GPU optimization...");
    const resizedImageBase64 = await resizeImage(imageBase64, 256, 256);

    // Generate a 256x256 white mask to match the resized image
    const maskBase64 = createWhiteMask(256, 256);
    
    console.log("[SAM 3D] Sending request to Optimized L4 Cluster...", {
       url: VERTEX_ENDPOINT_URL,
       originalSize: imageBase64.length,
       resizedSize: resizedImageBase64.length,
       maskSize: maskBase64.length
    });

    const response = await fetch(VERTEX_ENDPOINT_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': DEFAULT_VERTEX_TOKEN
      },
      body: JSON.stringify({
        image: resizedImageBase64,
        mask: maskBase64,
        seed: 42
      }),
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      let errorDetail = `Status ${response.status}`;
      try {
        const errorJson = await response.json();
        if (errorJson.detail) errorDetail = errorJson.detail;
        else if (errorJson.message) errorDetail = errorJson.message;
        else if (errorJson.error) errorDetail = typeof errorJson.error === 'string' ? errorJson.error : JSON.stringify(errorJson.error);
        else errorDetail = JSON.stringify(errorJson);
      } catch (e) {
        const errorText = await response.text().catch(() => null);
        if (errorText) errorDetail = errorText.substring(0, 200);
      }
      throw new Error(`SAM 3D Server Error: ${errorDetail}`);
    }

    // --- RESPONSE PARSING LOGIC (STRICT) ---
    // 1. Get the JSON response from the server
    const data = await response.json(); 
    const plyBase64 = data.ply;
    
    if (!plyBase64) {
      throw new Error("API response missing 'ply' field");
    }

    // Clean up base64 string
    const cleanBase64 = plyBase64.replace(/^data:.+;base64,/, '').replace(/\s/g, '');

    // 2. Decode Base64 -> Binary String
    const binaryString = atob(cleanBase64);
    
    // 3. Convert to Uint8Array (CRITICAL LOOP!)
    // This step fixes "corrupt file" issues by ensuring byte alignment
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }
    
    // 4. Create Blob from raw binary data
    console.log("3D Model generated, size:", bytes.length);
    return new Blob([bytes], { type: 'application/octet-stream' });

  } catch (error: any) {
    if (error.name === 'AbortError') {
      throw new Error('3D generation timed out after 5 minutes');
    }
    console.error('SAM 3D Pipeline Error:', error);
    throw error;
  }
}

/**
 * Tests if the endpoint is reachable.
 */
export const testEndpointConnection = async (endpointUrl: string): Promise<boolean> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 5000);

  try {
    await fetch(endpointUrl, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'X-API-Key': DEFAULT_VERTEX_TOKEN 
      },
      body: JSON.stringify({ ping: 'pong' }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    return true;
  } catch (error) {
    clearTimeout(timeoutId);
    return false;
  }
};
