# Example Outputs

This directory contains sample outputs from the Imagen Apex pipeline.

## Viewing 3D Models

PLY files can be viewed with:

- **Online:** [3dviewer.net](https://3dviewer.net) - Drag and drop your PLY file
- **MeshLab:** Free, cross-platform 3D mesh viewer
- **Blender:** File > Import > Stanford PLY

## Sample Prompts

Try these prompts to generate interesting 3D models:

```bash
# Vehicles
python -m src.pipeline --prompt "a red sports car" --output output/car.ply
python -m src.pipeline --prompt "a vintage motorcycle" --output output/motorcycle.ply

# Furniture
python -m src.pipeline --prompt "a wooden rocking chair" --output output/chair.ply
python -m src.pipeline --prompt "a modern desk lamp" --output output/lamp.ply

# Objects
python -m src.pipeline --prompt "a ceramic coffee mug" --output output/mug.ply
python -m src.pipeline --prompt "a golden trophy" --output output/trophy.ply
python -m src.pipeline --prompt "a vintage camera" --output output/camera.ply
```
