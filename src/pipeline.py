"""
Imagen Apex - Text-to-3D Pipeline

End-to-end pipeline that:
1. Generates an image from a text prompt using Nano Banana Pro
2. Creates an object mask for the generated image
3. Sends to SAM 3D Objects for 3D reconstruction
4. Saves the output as a PLY file
"""

import os
import argparse
from pathlib import Path
from typing import Optional, Dict, Callable

from .image_generator import ImageGenerator
from .sam3d_client import SAM3DClient
from .utils import get_env_or_default, ensure_directory


class TextTo3DPipeline:
    """
    Complete text-to-3D generation pipeline.
    
    Combines Nano Banana Pro image generation with SAM 3D Objects
    to convert text prompts directly into 3D models.
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        region: str = "us-central1",
        sam3d_endpoint: Optional[str] = None,
        sam3d_api_key: Optional[str] = None,
        prefer_nano_banana: bool = True
    ):
        """
        Initialize the pipeline.
        
        Args:
            project_id: Google Cloud project ID
            region: Google Cloud region for image generation
            sam3d_endpoint: SAM 3D endpoint URL or name
            sam3d_api_key: API key for SAM 3D endpoint
            prefer_nano_banana: Try Nano Banana Pro first for image generation
        """
        self.project_id = project_id or get_env_or_default("GCP_PROJECT_ID", "")
        self.region = region
        
        # Initialize components
        self.image_generator = ImageGenerator(
            project_id=self.project_id,
            region=self.region,
            prefer_nano_banana=prefer_nano_banana
        )
        
        self.sam3d_client = SAM3DClient(
            endpoint=sam3d_endpoint,
            api_key=sam3d_api_key,
            project_id=self.project_id
        )
    
    def generate(
        self,
        prompt: str,
        output_path: str,
        image_path: Optional[str] = None,
        save_intermediate: bool = True,
        seed: int = 42,
        progress_callback: Optional[Callable[[str, int], None]] = None
    ) -> Dict[str, str]:
        """
        Generate a 3D model from a text prompt.
        
        Args:
            prompt: Text description of the object to generate
            output_path: Path to save the output PLY file
            image_path: Optional pre-existing image (skips generation)
            save_intermediate: Save intermediate files (image, mask)
            seed: Random seed for reproducibility
            progress_callback: Optional callback(message, progress_percent)
            
        Returns:
            Dictionary with paths to all generated files
        """
        output_dir = Path(output_path).parent
        ensure_directory(str(output_dir))
        
        results = {}
        
        def _progress(message: str, percent: int):
            if progress_callback:
                progress_callback(message, percent)
            print(message)
        
        # Step 1: Generate or load image
        _progress("\n📷 Step 1: Preparing image...", 10)
        
        if image_path and Path(image_path).exists():
            _progress(f"   Using existing image: {image_path}", 20)
            generated_image_path = image_path
        else:
            _progress(f"   Generating from prompt: {prompt}", 15)
            generated_image_path = str(output_dir / "generated_image.png")
            self.image_generator.generate(
                prompt=prompt,
                output_path=generated_image_path
            )
            _progress(f"   ✅ Image generated", 40)
        
        results["image"] = generated_image_path
        
        # Step 2: Generate 3D model
        _progress("\n🔮 Step 2: Generating 3D model...", 50)
        
        ply_path = self.sam3d_client.generate_3d(
            image_path=generated_image_path,
            output_path=output_path,
            seed=seed
        )
        
        results["ply"] = ply_path
        _progress(f"   ✅ 3D model complete", 100)
        
        return results
    
    def generate_image_only(
        self,
        prompt: str,
        output_path: str,
        aspect_ratio: str = "1:1"
    ) -> str:
        """
        Generate only the image (skip 3D conversion).
        
        Args:
            prompt: Text description of the image
            output_path: Path to save the image
            aspect_ratio: Image aspect ratio
            
        Returns:
            Path to the generated image
        """
        return self.image_generator.generate(
            prompt=prompt,
            output_path=output_path,
            aspect_ratio=aspect_ratio
        )


def main():
    """CLI entry point for the pipeline."""
    parser = argparse.ArgumentParser(
        description="Imagen Apex - Text-to-3D Pipeline"
    )
    parser.add_argument("--prompt", help="Text prompt for generation")
    parser.add_argument("--image", help="Path to existing image (skip generation)")
    parser.add_argument("--output", default="output/model.ply", help="Output PLY path")
    parser.add_argument("--project", help="GCP project ID")
    parser.add_argument("--region", default="us-central1", help="GCP region")
    parser.add_argument("--endpoint", help="SAM 3D endpoint URL or name")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--image-only", 
        action="store_true", 
        help="Generate image only (skip 3D)"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.prompt and not args.image:
        parser.error("Either --prompt or --image must be provided")
    
    print("""
╔══════════════════════════════════════════════════════════╗
║               Imagen Apex - Text to 3D                   ║
╚══════════════════════════════════════════════════════════╝
""")
    
    pipeline = TextTo3DPipeline(
        project_id=args.project,
        region=args.region,
        sam3d_endpoint=args.endpoint
    )
    
    try:
        if args.image_only:
            output_path = args.output.replace(".ply", ".png")
            result = pipeline.generate_image_only(
                prompt=args.prompt,
                output_path=output_path
            )
            print(f"\n✅ Image saved: {result}")
        else:
            results = pipeline.generate(
                prompt=args.prompt,
                output_path=args.output,
                image_path=args.image,
                seed=args.seed
            )
            
            print(f"""
╔══════════════════════════════════════════════════════════╗
║                    Pipeline Complete!                    ║
╠══════════════════════════════════════════════════════════╣""")
            
            for key, path in results.items():
                print(f"║  {key}: {path:<50} ║")
            
            print("""╠══════════════════════════════════════════════════════════╣
║  View with: MeshLab, Blender, or https://3dviewer.net    ║
╚══════════════════════════════════════════════════════════╝
""")
            
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
