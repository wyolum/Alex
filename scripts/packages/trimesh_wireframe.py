import trimesh
import numpy as np
from numpy import linalg as la


def from_stl(stl_path, target_faces=1000, use_decimation=True):
    """
    Convert STL file to wireframe representation for 4-panel view.
    
    This function:
    1. Loads the STL file using trimesh
    2. Optionally decimates the mesh to reduce complexity
    3. Extracts silhouettes from 6 orthogonal views
    4. Normalizes to unit cube
    5. Returns wireframe with NaN separators
    
    Args:
        stl_path: Path to STL file
        target_faces: Target number of faces for decimation (default: 1000)
        use_decimation: Whether to decimate complex meshes (default: True)
    
    Returns:
        wireframe: nx3 numpy array with NaN separators between line segments
    """
    # Load mesh
    mesh = trimesh.load(stl_path, force='mesh')
    
    # Decimate if mesh is too complex
    original_faces = len(mesh.faces)
    if use_decimation and original_faces > target_faces:
        print(f"Decimating mesh: {original_faces} -> {target_faces} faces")
        mesh = mesh.simplify_quadric_decimation(target_faces)
    
    # Normalize mesh to unit cube centered at origin
    # Get bounding box
    bounds = mesh.bounds
    center = (bounds[0] + bounds[1]) / 2
    size = bounds[1] - bounds[0]
    max_size = np.max(size)
    
    # Center at origin with Z-min at 0
    center[2] = bounds[0][2]
    mesh.apply_translation(-center)
    mesh.apply_scale(1.0 / max_size)
    
    # Define 6 orthogonal view directions
    view_directions = {
        'top': np.array([0, 0, 1]),
        'bottom': np.array([0, 0, -1]),
        'front': np.array([0, 1, 0]),
        'back': np.array([0, -1, 0]),
        'right': np.array([1, 0, 0]),
        'left': np.array([-1, 0, 0])
    }
    
    # Extract silhouettes from each view
    all_wireframes = []
    
    for view_name, view_dir in view_directions.items():
        # Get outline (silhouette) for this view direction
        # outline() returns a Path3D object
        try:
            outline = mesh.outline(view_dir)
            
            if outline is not None and hasattr(outline, 'entities'):
                # outline is a Path3D with vertices and entities
                # Each entity is a line segment or path
                for entity in outline.entities:
                    # Get the points for this entity
                    points = outline.vertices[entity.points]
                    
                    # Add points to wireframe
                    for point in points:
                        all_wireframes.append(point)
                    
                    # Add NaN separator after each entity
                    all_wireframes.append([np.nan, np.nan, np.nan])
        except Exception as e:
            print(f"Warning: Could not get outline for {view_name} view: {e}")
            continue
    
    if not all_wireframes:
        # Fallback: use simplified edge-based approach
        print("Warning: No silhouettes found, using edge-based wireframe")
        return from_stl_simple(stl_path, target_faces)
    
    # Remove last separator
    wireframe = np.array(all_wireframes[:-1] if all_wireframes else [[np.nan, np.nan, np.nan]])
    
    return wireframe


def get_bounding_box_wireframe():
    """
    Return a simple bounding box wireframe as fallback.
    
    Returns:
        nx3 array representing a unit cube wireframe
    """
    # Unit cube edges
    vertices = np.array([
        [-0.5, -0.5, 0],
        [0.5, -0.5, 0],
        [0.5, 0.5, 0],
        [-0.5, 0.5, 0],
        [-0.5, -0.5, 1],
        [0.5, -0.5, 1],
        [0.5, 0.5, 1],
        [-0.5, 0.5, 1]
    ])
    
    # Define edges
    edges = [
        # Bottom face
        [0, 1], [1, 2], [2, 3], [3, 0],
        # Top face
        [4, 5], [5, 6], [6, 7], [7, 4],
        # Vertical edges
        [0, 4], [1, 5], [2, 6], [3, 7]
    ]
    
    wireframe = []
    for edge in edges:
        wireframe.append(vertices[edge[0]])
        wireframe.append(vertices[edge[1]])
        wireframe.append([np.nan, np.nan, np.nan])
    
    return np.array(wireframe[:-1])


def from_stl_simple(stl_path, max_faces=1000):
    """
    Simplified version: just get the decimated mesh edges.
    
    This is faster but shows all edges, not just silhouettes.
    Good for simple parts or as a fallback.
    
    Args:
        stl_path: Path to STL file
        max_faces: Maximum number of faces (will decimate if exceeded)
    
    Returns:
        wireframe: nx3 numpy array with NaN separators
    """
    # Load mesh
    mesh = trimesh.load(stl_path, force='mesh')
    
    original_faces = len(mesh.faces)
    
    # Decimate if needed
    if original_faces > max_faces:
        # Calculate reduction percentage (how much to REMOVE, not keep)
        # If we have 2000 faces and want 1000, we need to remove 50%
        reduction = 1.0 - (max_faces / original_faces)
        print(f"Decimating: {original_faces} faces -> ~{max_faces} faces (removing {reduction:.1%})")
        mesh = mesh.simplify_quadric_decimation(reduction)
        print(f"Result: {len(mesh.faces)} faces")
    
    # Normalize to unit cube (-0.5 to 0.5 in each dimension)
    # This ensures that when multiplied by [dim1, dim2, length], we get the correct shape
    bounds = mesh.bounds
    center = (bounds[0] + bounds[1]) / 2
    center[2] = bounds[0][2]  # Keep Z-min at 0
    size = bounds[1] - bounds[0]
    
    # Translate to origin
    mesh.apply_translation(-center)
    
    # Scale each dimension independently to fit in -0.5 to 0.5 range
    # This preserves the aspect ratio when later multiplied by [dim1, dim2, length]
    scale_factors = np.where(size > 0, 1.0 / size, 1.0)
    mesh.apply_scale(scale_factors)
    
    # Get all unique edges
    edges = mesh.edges_unique
    
    print(f"Mesh has {len(edges)} unique edges")
    
    # Convert to wireframe format
    wireframe = []
    for edge in edges:
        v1, v2 = mesh.vertices[edge]
        wireframe.append(v1)
        wireframe.append(v2)
        wireframe.append([np.nan, np.nan, np.nan])
    
    return np.array(wireframe[:-1] if wireframe else [[np.nan, np.nan, np.nan]])



# For testing
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        stl_file = sys.argv[1]
    else:
        stl_file = '../part_libraries/Main/STL/2020 Alex.stl'
    
    print(f"Loading: {stl_file}")
    wf = from_stl(stl_file)
    print(f"Wireframe shape: {wf.shape}")
    print(f"Bounds: {np.nanmin(wf, axis=0)} to {np.nanmax(wf, axis=0)}")
    
    # Visualize
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    # Plot wireframe
    ax.plot(wf[:, 0], wf[:, 1], wf[:, 2], 'b-', linewidth=0.5)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_title(f'Trimesh Wireframe: {stl_file}')
    
    plt.show()
