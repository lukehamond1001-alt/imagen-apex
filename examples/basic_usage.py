"""
Basic Usage Example

Demonstrates the simplest way to use Imagen Apex for text-to-3D generation.
"""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pipeline import TextTo3DPipeline


def main():
    """
    Generate a 3D model from a text prompt.
    
    Make sure you have:
    1. Configured your .env file with credentials
    2. Deployed the SAM 3D endpoint (see deploy/ scripts)
    """
    
    # Initialize the pipeline
    # Credentials are loaded from .env or environment variables
    pipeline = TextTo3DPipeline()
    
    # Example prompts to try
    prompts = [
        "a red sports car",
        "a wooden treasure chest",
        "a ceramic coffee mug",
        "a vintage camera",
        "a golden crown",
    ]
    
    # Generate from the first prompt
    prompt = prompts[0]
    output_path = f"examples/outputs/{prompt.replace(' ', '_')}.ply"
    
    print(f"Generating 3D model for: '{prompt}'")
    print("-" * 50)
    
    try:
        results = pipeline.generate(
            prompt=prompt,
            output_path=output_path,
            seed=42
        )
        
        print("\n✅ Generation complete!")
        print(f"   Image: {results['image']}")
        print(f"   3D Model: {results['ply']}")
        print("\n💡 View your 3D model at: https://3dviewer.net")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your .env configuration")
        print("  2. Ensure SAM 3D endpoint is deployed")
        print("  3. Verify GCP credentials are set up")


if __name__ == "__main__":
    main()
