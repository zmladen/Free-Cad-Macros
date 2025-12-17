import FreeCAD as App
import FreeCADGui as Gui
import Part
import MeshPart
import os

print("\n🔥 MACRO RELOADED 🔥")
print("===== FACE COLOR → STL EXPORT (AUTO) =====\n")

# ================================================================
# CONFIGURATION
# ================================================================
TARGET_LABELS = ["Hub",
                "Shroud",
                "Spiral"
            ]
EXPORT_DIR = r"C:\exports\stl"             # STL export directory

# Color definitions (RGB tuples, values 0.0 to 1.0)
INLET_COLOR = (1.0, 1.0, 0.0)             # Yellow
OUTLET_COLOR = (1.0, 0.0, 0.0)            # Red
COLOR_TOLERANCE = 1e-4                     # Color matching tolerance

# Mesh settings
MESH_LINEAR_DEFLECTION = 0.05             # Finer = 0.01 (very fine)
MESH_ANGULAR_DEFLECTION = 0.1             # Finer = lower value
MESH_RELATIVE = False

# ================================================================
# HELPER FUNCTIONS
# ================================================================

def find_body_by_label(doc, target_label):
    """
    Find a Body by label, handling both direct Bodies and Bodies inside Parts.
    Returns: Body object or None
    """
    part = None
    body = None
    
    for o in doc.Objects:
        if o.Label == target_label:
            if o.TypeId == "App::Part":
                part = o
            elif o.TypeId == "PartDesign::Body":
                body = o
            break
    
    if body:
        print(f"✔ Using Body directly: {body.Label}")
        return body
    elif part:
        bodies = [o for o in part.Group if o.TypeId == "PartDesign::Body"]
        if not bodies:
            raise RuntimeError(f"❌ Part '{part.Label}' has no Body")
        print(f"✔ Using Body from Part '{part.Label}': {bodies[0].Label}")
        return bodies[0]
    else:
        raise RuntimeError(f"❌ No Part or Body with Label '{target_label}' found")


def get_face_colors(body):
    """
    Extract face colors from the Body's Tip feature.
    Returns: (faces, colors)
    """
    if not body.Tip or not hasattr(body.Tip, "Shape"):
        raise RuntimeError("❌ Body has no valid Tip")
    
    shape = body.Tip.Shape
    faces = shape.Faces
    
    vo = body.Tip.ViewObject
    if not hasattr(vo, "DiffuseColor"):
        raise RuntimeError("❌ Feature has no DiffuseColor")
    
    colors = vo.DiffuseColor
    
    if len(colors) != len(faces):
        raise RuntimeError(
            f"❌ Color count ({len(colors)}) does not match face count ({len(faces)})"
        )
    
    print(f"✔ Face count: {len(faces)}")
    print(f"✔ Colored faces on feature: {len(colors)}")
    
    return faces, colors


def is_color_match(rgb, target, tolerance):
    """Check if RGB color matches target within tolerance."""
    return all(abs(rgb[i] - target[i]) < tolerance for i in range(3))


def classify_faces(faces, colors, inlet_color, outlet_color, tolerance):
    """
    Classify faces into inlet, outlet, and body groups based on colors.
    Returns: (inlet_ids, outlet_ids, body_ids)
    """
    inlet_ids = []
    outlet_ids = []
    body_ids = []
    
    for i in range(len(faces)):
        fid = i + 1
        rgb = colors[i][:3]
        
        if is_color_match(rgb, inlet_color, tolerance):
            inlet_ids.append(fid)
        elif is_color_match(rgb, outlet_color, tolerance):
            outlet_ids.append(fid)
        else:
            body_ids.append(fid)
    
    return inlet_ids, outlet_ids, body_ids


def mesh_faces(body, faces, face_ids, suffix, export_dir, linear_deflection, angular_deflection, relative):
    """
    Mesh and export a group of faces to STL.
    """
    if not face_ids:
        print(f"⚠ No faces for {suffix}, skipping")
        return
    
    filename = f"{body.Label}_{suffix}.stl"
    path = os.path.join(export_dir, filename)
    
    print(f"→ Writing STL to: {path}")
    
    gp = body.getGlobalPlacement()
    face_shapes = [
        faces[i - 1].copy().transformGeometry(gp.toMatrix())
        for i in face_ids
    ]
    
    if len(face_shapes) == 1:
        shape_to_mesh = face_shapes[0]
    else:
        shape_to_mesh = Part.Shell(face_shapes)
    
    mesh = MeshPart.meshFromShape(
        Shape=shape_to_mesh,
        LinearDeflection=linear_deflection,
        AngularDeflection=angular_deflection,
        Relative=relative
    )
    
    mesh.write(path)
    print(f"✔ Exported: {path}")


# ================================================================
# MAIN EXECUTION
# ================================================================

def main():
    # Setup
    os.makedirs(EXPORT_DIR, exist_ok=True)
    print("✔ STL files will be exported to:")
    print(f"  {EXPORT_DIR}\n")
    
    # Get document
    doc = App.ActiveDocument
    if not doc:
        raise RuntimeError("❌ No active document")
    
    # Process each target label
    processed = []
    failed = []
    
    for idx, target_label in enumerate(TARGET_LABELS, 1):
        print(f"\n{'='*60}")
        print(f"Processing {idx}/{len(TARGET_LABELS)}: '{target_label}'")
        print(f"{'='*60}\n")
        
        try:
            # Find body
            body = find_body_by_label(doc, target_label)
            
            # Get faces and colors
            faces, colors = get_face_colors(body)
            
            # Classify faces
            inlet_ids, outlet_ids, body_ids = classify_faces(
                faces, colors,
                INLET_COLOR, OUTLET_COLOR, COLOR_TOLERANCE
            )
            
            print("\n===== FACE GROUPS =====")
            print(f"Inlet faces : {inlet_ids}")
            print(f"Outlet faces: {outlet_ids}")
            print(f"Body faces  : {body_ids}")
            
            # Export STL files
            mesh_faces(body, faces, inlet_ids, "inlet", EXPORT_DIR,
                       MESH_LINEAR_DEFLECTION, MESH_ANGULAR_DEFLECTION, MESH_RELATIVE)
            mesh_faces(body, faces, outlet_ids, "outlet", EXPORT_DIR,
                       MESH_LINEAR_DEFLECTION, MESH_ANGULAR_DEFLECTION, MESH_RELATIVE)
            mesh_faces(body, faces, body_ids, "body", EXPORT_DIR,
                       MESH_LINEAR_DEFLECTION, MESH_ANGULAR_DEFLECTION, MESH_RELATIVE)
            
            processed.append(target_label)
            print(f"\n✔ Successfully processed: '{target_label}'")
            
        except Exception as e:
            failed.append((target_label, str(e)))
            print(f"\n❌ Failed to process '{target_label}': {e}")
            print("Continuing with next body...\n")
    
    # Summary
    print(f"\n{'='*60}")
    print("===== SUMMARY =====")
    print(f"{'='*60}")
    print(f"Processed successfully: {len(processed)}/{len(TARGET_LABELS)}")
    if processed:
        print(f"  {', '.join(processed)}")
    if failed:
        print(f"\nFailed: {len(failed)}")
        for label, error in failed:
            print(f"  '{label}': {error}")
    print(f"\n===== DONE =====\n")


if __name__ == "__main__":
    main()
else:
    # When run as FreeCAD macro, execute directly
    main()
