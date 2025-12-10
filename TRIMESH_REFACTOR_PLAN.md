# Trimesh Refactoring Plan for 4-Panel View Optimization

## Current Situation
- Custom edge-tracing algorithm in `stl_to_wireframe.py`
- Can be slow for complex STL files
- Uses perimeter extraction which is O(n²) in worst case

## Proposed Solution: Use Trimesh

### Benefits of Trimesh:
1. **Silhouette Extraction** - Fast outline extraction from any viewing angle
2. **Mesh Decimation** - Reduce triangle count while preserving shape
3. **2D Projections** - Efficient 3D → 2D projection
4. **Shadow Casting** - Can compute shadows/silhouettes
5. **Performance** - Optimized C/Cython backend

### Implementation Strategy:

#### Phase 1: Create New Trimesh-Based Wireframe Generator
```python
# New file: packages/trimesh_wireframe.py

import trimesh
import numpy as np

def stl_to_wireframe_trimesh(stl_path, target_faces=500):
    """
    Convert STL to wireframe using trimesh.
    
    Args:
        stl_path: Path to STL file
        target_faces: Target number of faces for decimation
    
    Returns:
        wireframe: nx3 array with NaN separators
    """
    # Load mesh
    mesh = trimesh.load(stl_path)
    
    # Decimate if too complex
    if len(mesh.faces) > target_faces:
        mesh = mesh.simplify_quadric_decimation(target_faces)
    
    # Get silhouettes from 6 orthogonal views
    views = [
        [1, 0, 0],   # +X (right)
        [-1, 0, 0],  # -X (left)
        [0, 1, 0],   # +Y (front)
        [0, -1, 0],  # -Y (back)
        [0, 0, 1],   # +Z (top)
        [0, 0, -1]   # -Z (bottom)
    ]
    
    wireframes = []
    for view_dir in views:
        # Get silhouette edges for this view
        silhouette = mesh.outline(view_dir)
        
        # Convert to 3D coordinates
        # ... project back to 3D
        
        wireframes.append(silhouette_3d)
    
    # Combine all wireframes with NaN separators
    return combine_wireframes(wireframes)
```

#### Phase 2: Hybrid Approach (Recommended)
- Use trimesh for **complex** parts (>1000 triangles)
- Keep existing algorithm for **simple** parts (fast enough)
- Add caching to avoid regenerating wireframes

#### Phase 3: Shadow Casting for Better Visualization
```python
def get_shadow_outline(mesh, view_direction):
    """Get the shadow outline (silhouette) from a viewing direction."""
    # Trimesh can compute this efficiently
    outline = mesh.outline(view_direction)
    return outline
```

### Migration Path:

1. **Create new module** (`trimesh_wireframe.py`)
2. **Add feature flag** to switch between old/new
3. **Test with complex parts** (>5000 triangles)
4. **Benchmark performance**
5. **Gradually migrate** if performance is better

### Performance Targets:
- Complex STL (10k triangles): < 0.5 seconds
- Decimated mesh: ~500 faces
- 4-panel view refresh: < 100ms

### Code Structure:
```
packages/
  ├── stl_to_wireframe.py      # Current (keep for now)
  ├── trimesh_wireframe.py     # New trimesh-based
  └── wireframe_factory.py     # Chooses best method
```

## Next Steps:
1. Create `trimesh_wireframe.py` with basic implementation
2. Test with a complex STL file
3. Compare performance with current method
4. Decide on migration strategy

## Questions to Answer:
- What's the triangle count threshold for switching methods?
- Should we cache wireframes to disk?
- Do we need different decimation levels for different zoom levels?
- Should silhouettes be view-dependent (update on rotation)?
