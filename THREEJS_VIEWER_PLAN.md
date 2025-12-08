# Three.js 3D Viewer Implementation Plan

**Goal:** Add an interactive 3D viewer panel to AlexCAD using Three.js for real-time visualization

**Status:** 🚧 IN PROGRESS  
**Started:** 2025-12-08  
**Estimated Time:** 4-6 hours

---

## 🎯 Objectives

### Primary Goals
1. Add a 5th panel with Three.js 3D viewer
2. Real-time updates when design changes
3. Interactive camera controls (orbit, pan, zoom)
4. Better visualization than current OpenSCAD views

### Secondary Goals
- Export 3D view as image
- Toggle wireframe/solid view
- Lighting controls
- Part highlighting on hover
- Measurement tools

---

## 🏗️ Architecture Options

### Option 1: Embedded Web View (Recommended)
**Approach:** Use tkinter webview or CEF (Chromium Embedded Framework)

**Pros:**
- Full Three.js capabilities
- Easy to update/maintain
- Rich ecosystem of Three.js plugins
- Can use modern web features

**Cons:**
- Requires webview library
- Communication between Python and JS
- Larger dependency footprint

**Libraries:**
- `cefpython3` - Chromium Embedded Framework
- `pywebview` - Lightweight webview wrapper
- `tkinterweb` - Tkinter-specific HTML renderer

### Option 2: VTK (Visualization Toolkit)
**Approach:** Use VTK for 3D rendering directly in Python

**Pros:**
- Pure Python solution
- No web dependencies
- Powerful 3D capabilities
- Good Tkinter integration

**Cons:**
- Steeper learning curve
- Less modern than Three.js
- Harder to customize UI

**Libraries:**
- `vtk` - Visualization Toolkit
- `pyvista` - VTK wrapper (easier API)

### Option 3: Matplotlib 3D
**Approach:** Use matplotlib's 3D plotting

**Pros:**
- Already familiar to Python developers
- Easy integration
- Lightweight

**Cons:**
- Limited interactivity
- Not designed for CAD
- Performance issues with complex models

---

## 📋 Recommended Approach: pywebview + Three.js

### Why This Choice?
1. **Modern & Powerful:** Full Three.js ecosystem
2. **Lightweight:** pywebview is simpler than CEF
3. **Cross-platform:** Works on Linux, Windows, macOS
4. **Easy Communication:** Python ↔ JavaScript bridge
5. **Future-proof:** Can add WebGL features easily

---

## 🔧 Implementation Steps

### Phase 1: Setup & Integration (2 hours)

#### Step 1: Install Dependencies
```bash
pip install pywebview
```

#### Step 2: Create HTML/JS Template
Create `scripts/packages/viewer3d/index.html`:
- Three.js from CDN
- Basic scene setup
- Camera controls (OrbitControls)
- Lighting setup

#### Step 3: Create Python Wrapper
Create `scripts/packages/viewer3d.py`:
- WebView window management
- Python ↔ JS communication
- Scene update methods

#### Step 4: Integrate with AlexCAD
Modify `scripts/AlexCAD.py`:
- Add 5th panel for 3D viewer
- Connect to scene updates
- Handle window resizing

### Phase 2: STL Loading & Display (1.5 hours)

#### Step 5: STL Export from Scene
- Export current scene to STL
- Use existing STL export functionality
- Temporary file or in-memory transfer

#### Step 6: Three.js STL Loader
- Load STL files in Three.js
- Display in scene
- Apply materials and lighting

#### Step 7: Real-time Updates
- Watch for scene changes
- Reload STL when design updates
- Smooth transitions

### Phase 3: Interactivity (1.5 hours)

#### Step 8: Camera Controls
- OrbitControls for mouse interaction
- Zoom, pan, rotate
- Reset camera button

#### Step 9: View Presets
- Top, Front, Side, Iso views
- Smooth camera transitions
- Keyboard shortcuts

#### Step 10: Visual Enhancements
- Grid helper
- Axes helper
- Shadows
- Ambient occlusion (optional)

### Phase 4: Advanced Features (1 hour)

#### Step 11: Export Options
- Screenshot of 3D view
- Export as GLB/GLTF
- Share view link (future)

#### Step 12: Measurement Tools
- Distance measurement
- Angle measurement
- Bounding box display

---

## 📐 UI Layout

### Current 4-Panel Layout:
```
┌──────────┬──────────┐
│   Top    │   Iso    │
├──────────┼──────────┤
│  Front   │   Side   │
└──────────┴──────────┘
```

### New 5-Panel Layout (Option A - Vertical):
```
┌──────────┬──────────┬──────────┐
│   Top    │   Iso    │          │
├──────────┼──────────┤          │
│  Front   │   Side   │ Three.js │
└──────────┴──────────┤   3D     │
                      │  Viewer  │
                      └──────────┘
```

### New 5-Panel Layout (Option B - Horizontal):
```
┌──────────┬──────────┐
│   Top    │   Iso    │
├──────────┼──────────┤
│  Front   │   Side   │
├──────────┴──────────┤
│   Three.js 3D View  │
└─────────────────────┘
```

### New 5-Panel Layout (Option C - Tabbed):
```
┌──────────┬──────────┐
│   Top    │   Iso    │
├──────────┼──────────┤
│  Front   │   Side   │
└──────────┴──────────┘
[2D Views] [3D View] ← Tabs
```

**Recommendation:** Option A (Vertical) - Keeps all views visible simultaneously

---

## 🔌 Python ↔ JavaScript Communication

### From Python to JS:
```python
# Update 3D scene with new STL
viewer.update_scene(stl_data)

# Set camera view
viewer.set_view('top')

# Highlight part
viewer.highlight_part(part_id)
```

### From JS to Python:
```javascript
// User clicked on part
pywebview.api.on_part_clicked(partId)

// Camera position changed
pywebview.api.on_camera_moved(position)
```

---

## 📦 File Structure

```
scripts/packages/viewer3d/
├── __init__.py           # Python module
├── viewer.py             # WebView wrapper
├── index.html            # Three.js viewer
├── viewer.js             # Three.js logic
├── styles.css            # Viewer styling
└── assets/
    └── grid.png          # Textures, icons, etc.
```

---

## 🎨 Three.js Scene Setup

### Basic Scene Components:
```javascript
// Scene
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xf0f0f0);

// Camera
const camera = new THREE.PerspectiveCamera(
    75,                                    // FOV
    window.innerWidth / window.innerHeight, // Aspect
    0.1,                                   // Near
    1000                                   // Far
);

// Renderer
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.shadowMap.enabled = true;

// Lights
const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);

// Controls
const controls = new OrbitControls(camera, renderer.domElement);

// Grid
const gridHelper = new THREE.GridHelper(1000, 100);
```

---

## 🧪 Testing Checklist

### Phase 1:
- [ ] pywebview installs correctly
- [ ] WebView window opens
- [ ] Three.js loads from CDN
- [ ] Basic scene renders
- [ ] Panel integrates with AlexCAD

### Phase 2:
- [ ] STL export works
- [ ] STL loads in Three.js
- [ ] Model displays correctly
- [ ] Materials look good
- [ ] Updates on scene change

### Phase 3:
- [ ] Mouse controls work (orbit, pan, zoom)
- [ ] View presets work
- [ ] Keyboard shortcuts work
- [ ] Visual helpers display correctly

### Phase 4:
- [ ] Screenshot export works
- [ ] Measurements are accurate
- [ ] Performance is acceptable

---

## ⚡ Performance Considerations

### Optimization Strategies:
1. **Lazy Loading:** Only load 3D view when tab is active
2. **LOD (Level of Detail):** Simplify geometry for large assemblies
3. **Instancing:** Reuse geometry for repeated parts
4. **Frustum Culling:** Don't render off-screen objects
5. **Debouncing:** Limit update frequency during rapid changes

### Target Performance:
- **60 FPS** for models with < 100 parts
- **30 FPS** for models with 100-500 parts
- **Acceptable** for models with 500+ parts

---

## 🚀 Future Enhancements

### Post-MVP Features:
- [ ] AR/VR support (WebXR)
- [ ] Animation timeline
- [ ] Assembly instructions view
- [ ] Exploded view
- [ ] Section cuts
- [ ] Material editor
- [ ] Lighting presets
- [ ] Background environments
- [ ] Collaborative viewing (multi-user)

---

## 📚 Resources

### Documentation:
- [Three.js Docs](https://threejs.org/docs/)
- [pywebview Docs](https://pywebview.flowrl.com/)
- [OrbitControls](https://threejs.org/docs/#examples/en/controls/OrbitControls)
- [STLLoader](https://threejs.org/docs/#examples/en/loaders/STLLoader)

### Examples:
- [Three.js Examples](https://threejs.org/examples/)
- [CAD Viewer Example](https://threejs.org/examples/#webgl_loader_stl)

---

## 🎯 Success Metrics

### User Experience:
- ✅ Smooth 60 FPS rendering
- ✅ Intuitive camera controls
- ✅ Real-time updates (< 1 second lag)
- ✅ Clear visual feedback

### Technical:
- ✅ < 100 MB memory footprint
- ✅ < 2 second initial load time
- ✅ Works on Linux, Windows, macOS
- ✅ No crashes or freezes

### Adoption:
- ✅ Users prefer 3D view over 2D views
- ✅ Reduces design errors
- ✅ Speeds up design iteration

---

## 🏁 Next Steps

1. **Install pywebview** and test basic integration
2. **Create HTML template** with Three.js
3. **Build Python wrapper** for WebView
4. **Integrate with AlexCAD** panel system
5. **Test with real designs**

**Let's start with Phase 1!** 🚀
