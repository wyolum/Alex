# Branch: fix/path-issues-and-json-export

This branch contains improvements to the Alex CAD project:

## 1. JSON Parts Library Export

A complete export of the parts database in JSON format:

**Location**: `part_libraries/parts_library.json`

**Contents**:
- 15 parts from the Main library
- 8 fixed-price parts (connectors and plates)
- 7 aluminum extrusions with piecewise pricing based on length
- Interface definitions for part connections
- Complete specifications (dimensions, colors, STL files, purchase URLs)

**Usage**: This JSON file can be used for:
- Importing parts into other CAD systems
- Web-based part catalogs
- API endpoints for part data
- Data exchange with other applications

## 2. Path Fixes for Cross-Directory Execution

Fixed hardcoded relative paths to use absolute paths, allowing AlexCAD to run from any directory.

**Files Modified**:
- `scripts/packages/parts_db.py` - Fixed piecewise.csv path
- `scripts/AlexCAD.py` - Fixed alignment button and icon image paths
- `scripts/packages/view_layout.py` - Fixed rotation button image paths

**Benefit**: The application now works regardless of the current working directory.

## 3. Tooltips for Better UX

Added comprehensive tooltips to all buttons and controls:

**New File**: `scripts/packages/tooltip.py` - Tooltip utility module

**Tooltips Added**:
- Sidebar controls (New Part, Length, Dimensions, Step)
- Zoom buttons (Zoom In, Zoom Out, Zoom Fit, Mirror Z)
- All 15 alignment buttons (X, Y, Z axis operations)

**Benefit**: Users can now hover over any button to see what it does.

## 4. Complete Wireframe Files

Added missing wireframe files from the wireframes.npz archive:

**Files Added**:
- `Cylinder.npy` - Cylinder wireframe
- `Cone.npy` - Cone wireframe  
- `T-Plate.npy` - T-Plate wireframe
- `Corner-Plate.npy` - Corner plate wireframe

**Benefit**: All wireframe shapes are now available for part creation.

## 5. Comprehensive Test Suite

Created 57 unit tests for JSON functionality:

**Test Files**:
- `tests/test_json_parts_library.py` - 29 tests for JSON structure
- `tests/test_json_export_import.py` - 28 tests for export/import

**Test Coverage**:
- JSON structure validation
- Part data integrity
- Piecewise pricing
- Interface definitions
- Database consistency
- Export/import operations

**Result**: 57/57 tests passing (100%)

## Running AlexCAD

### On this branch (fix/path-issues-and-json-export):
```bash
# Can run from project root or any directory
conda activate alex_test
python3 scripts/AlexCAD.py
```

### On main branch:
```bash
# Must run from scripts/ directory
cd scripts
conda activate alex_test
python3 AlexCAD.py
```

## Branch Comparison

| Feature | main | fix/path-issues-and-json-export |
|---------|------|--------------------------------|
| JSON parts library | ❌ | ✅ |
| Run from any directory | ❌ | ✅ |
| Run from scripts/ directory | ✅ | ✅ |

## Switching Branches

```bash
# Switch to this branch
git checkout fix/path-issues-and-json-export

# Switch back to main
git checkout main
```
