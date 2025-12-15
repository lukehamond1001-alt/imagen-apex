"""
Utility functions for Imagen Apex pipeline.
"""

import os
import base64
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
from PIL import Image


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64 string.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded string of the image
    """
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def decode_base64_to_image(base64_string: str) -> Image.Image:
    """
    Decode a base64 string to PIL Image.
    
    Args:
        base64_string: Base64 encoded image data
        
    Returns:
        PIL Image object
    """
    image_data = base64.b64decode(base64_string)
    return Image.open(BytesIO(image_data))


def save_base64_to_file(base64_string: str, output_path: str) -> None:
    """
    Save base64 encoded data to a file.
    
    Args:
        base64_string: Base64 encoded data
        output_path: Path to save the file
    """
    data = base64.b64decode(base64_string)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(data)


def create_elliptical_mask(
    width: int, 
    height: int, 
    coverage: float = 0.6
) -> np.ndarray:
    """
    Create an elliptical mask centered in the image.
    
    Args:
        width: Image width
        height: Image height
        coverage: Fraction of image to cover (0.0-1.0)
        
    Returns:
        NumPy array mask (255 for object, 0 for background)
    """
    mask = np.zeros((height, width), dtype=np.uint8)
    
    center_x, center_y = width // 2, height // 2
    radius_x = int(width * coverage / 2)
    radius_y = int(height * coverage / 2)
    
    y, x = np.ogrid[:height, :width]
    ellipse = ((x - center_x) ** 2 / radius_x ** 2 + 
               (y - center_y) ** 2 / radius_y ** 2) <= 1
    mask[ellipse] = 255
    
    return mask


def resize_image(
    image_path: str, 
    size: Tuple[int, int] = (256, 256),
    output_path: Optional[str] = None
) -> str:
    """
    Resize an image to the specified size.
    
    Args:
        image_path: Path to the source image
        size: Target size as (width, height)
        output_path: Optional output path (uses temp if not provided)
        
    Returns:
        Path to the resized image
    """
    img = Image.open(image_path)
    img_resized = img.resize(size, Image.Resampling.LANCZOS)
    
    if output_path is None:
        output_path = str(Path(image_path).with_suffix(".resized.png"))
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img_resized.save(output_path)
    
    return output_path


def get_env_or_default(key: str, default: str) -> str:
    """
    Get environment variable with fallback to default.
    
    Args:
        key: Environment variable name
        default: Default value if not set
        
    Returns:
        Environment variable value or default
    """
    return os.environ.get(key, default)


def ensure_directory(path: str) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path
        
    Returns:
        Path object for the directory
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path
