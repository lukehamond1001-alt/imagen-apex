"""
Batch Generation Example

Generate multiple 3D models from a list of prompts.
"""

import os
import sys
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.pipeline import TextTo3DPipeline


def generate_single(
    pipeline: TextTo3DPipeline,
    prompt: str,
    output_dir: str,
    index: int
) -> dict:
    """Generate a single 3D model."""
    safe_name = prompt.lower().replace(" ", "_")[:30]
    output_path = f"{output_dir}/{index:03d}_{safe_name}.ply"
    
    try:
        result = pipeline.generate(
            prompt=prompt,
            output_path=output_path
        )
        return {
            "status": "success",
            "prompt": prompt,
            "output": result["ply"]
        }
    except Exception as e:
        return {
            "status": "error",
            "prompt": prompt,
            "error": str(e)
        }


def main():
    parser = argparse.ArgumentParser(description="Batch 3D model generation")
    parser.add_argument(
        "--prompts", 
        nargs="+", 
        default=[
            "a red sports car",
            "a wooden chair",
            "a ceramic vase",
            "a vintage telephone",
            "a golden trophy"
        ],
        help="List of prompts"
    )
    parser.add_argument("--output-dir", default="examples/outputs/batch")
    parser.add_argument("--parallel", type=int, default=1, help="Parallel workers")
    
    args = parser.parse_args()
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║           Imagen Apex - Batch Generation                 ║
╚══════════════════════════════════════════════════════════╝

Prompts: {len(args.prompts)}
Output: {args.output_dir}
""")
    
    # Ensure output directory exists
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Initialize pipeline
    pipeline = TextTo3DPipeline()
    
    results = []
    
    if args.parallel > 1:
        # Parallel execution
        with ThreadPoolExecutor(max_workers=args.parallel) as executor:
            futures = {
                executor.submit(
                    generate_single, pipeline, prompt, args.output_dir, i
                ): prompt
                for i, prompt in enumerate(args.prompts)
            }
            
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                status = "✅" if result["status"] == "success" else "❌"
                print(f"{status} {result['prompt']}")
    else:
        # Sequential execution
        for i, prompt in enumerate(args.prompts):
            print(f"\n[{i+1}/{len(args.prompts)}] Processing: {prompt}")
            result = generate_single(pipeline, prompt, args.output_dir, i)
            results.append(result)
            status = "✅" if result["status"] == "success" else "❌"
            print(f"{status} Complete")
    
    # Summary
    successful = sum(1 for r in results if r["status"] == "success")
    print(f"""
╔══════════════════════════════════════════════════════════╗
║                    Batch Complete                        ║
╠══════════════════════════════════════════════════════════╣
║  Successful: {successful}/{len(args.prompts):<44} ║
║  Output: {args.output_dir:<48} ║
╚══════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()
