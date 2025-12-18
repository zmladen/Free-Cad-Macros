# FreeCAD STL Export Macro

Automatically exports STL files from FreeCAD Bodies by classifying faces based on their colors.

## Overview

The script processes FreeCAD Bodies (Hub, Shroud, Spiral) and:
1. Extracts all faces from each Body's Tip feature
2. Reads face colors from the ViewObject's DiffuseColor property
3. Classifies faces into three groups:
   - **Inlet**: Yellow faces (RGB: 1.0, 1.0, 0.0)
   - **Outlet**: Red faces (RGB: 1.0, 0.0, 0.0)
   - **Body**: All other faces
4. Meshes and exports each group to separate STL files

## How It Works

The script automates the manual GUI procedure:
- **Manual**: Select face → Part → Create a copy → Create shape element copy
- **Script**: Automatically processes all faces, creates shape element copies, and meshes them

This is why the mesher can successfully mesh the selected surfaces - the script creates proper shape element copies for each face group.

## Configuration

Edit `export_stl.py` to configure:
- `TARGET_LABELS`: List of Body/Part labels to process
- `EXPORT_DIR`: Output directory for STL files
- `INLET_COLOR` / `OUTLET_COLOR`: RGB color values (0.0-1.0)
- `MESH_LINEAR_DEFLECTION` / `MESH_ANGULAR_DEFLECTION`: Mesh quality settings

## Requirements

- Each face must have an explicit color assigned (color count must match face count)
- Bodies must have a valid Tip feature with a Shape
- Face colors must be set via the ViewObject's DiffuseColor property
