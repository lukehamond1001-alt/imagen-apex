"""
Imagen Apex - Text-to-3D Generation Pipeline

Transform text prompts into stunning 3D models using:
- Google's Nano Banana Pro (Gemini image generation)
- Meta's SAM 3D Objects (image-to-3D reconstruction)
"""

__version__ = "1.0.0"
__author__ = "Luke Hamond"

from .pipeline import TextTo3DPipeline
from .image_generator import ImageGenerator
from .sam3d_client import SAM3DClient

__all__ = ["TextTo3DPipeline", "ImageGenerator", "SAM3DClient"]
