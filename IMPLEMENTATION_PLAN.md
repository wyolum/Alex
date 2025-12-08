# Alex CAD Implementation Plan

## Vision
Transform Alex CAD from a desktop CAD tool into a collaborative, cloud-enabled platform for aluminum extrusion design with modern 3D visualization and community-driven parts library.

## Phase 1: Parts Library Management 📦

### 1.1 Structured Parts Database ✅ IN PROGRESS
**Goal:** Replace hardcoded parts with a dynamic, extensible parts library

**Status:**
- ✅ JSON-based part definitions (`parts_library.json`)
- ✅ Part metadata (dimensions, weight, cost, supplier links)
- ✅ JSON export/import module (`json_export.py`)
- ✅ Comprehensive test suite (57 tests, 100% passing)
- 🔄 Hot-reload parts without restarting (NEXT)
- 🔄 Search and filter capabilities (NEXT)
- ✅ Part preview thumbnails (already exists)

**File Structure:**
```
~/.alex/
├── parts/
│   ├── extrusions/
│   │   ├── 2020.json
│   │   ├── 2040.json
│   │   └── custom_profile.json
│   ├── fasteners/
│   │   ├── m5_tnut.json
│   │   └── m5_bolt.json
│   └── brackets/
│       └── corner_bracket.json
└── config.yaml
```

### 1.2 Parts Editor UI 🔜 UPCOMING
**Goal:** GUI for creating/editing parts without code

**Features:**
- Visual part parameter editor
- Real-time preview
- Import from STEP/STL files
- Export to library
- Validation and testing

## Phase 2: Design Sharing & Collaboration 🌐

### 2.1 Cloud Storage Integration
**Goal:** Save/load designs from cloud storage

**Options:**
- GitHub Integration (Best for open source)
- Self-hosted WebDAV
- Hybrid Approach (local-first with sync)

### 2.2 Design Gallery
**Goal:** Browse and download community designs

**Features:**
- Web-based gallery at wyolum.com/alex/gallery
- Thumbnail previews
- Search by tags, parts used, complexity
- Like/favorite designs
- Download as .alex file
- "Remix" button (fork design)

### 2.3 Link Management
**Goal:** Keep supplier links up-to-date automatically

**Features:**
- Automated link checking
- Fallback suppliers
- Price tracking
- Availability notifications

## Phase 3: Enhanced OpenSCAD Integration 🎨

### 3.1 Improved OpenSCAD Rendering
**Goal:** Keep 4-panel view, add 5th panel for 3D preview

**Recommended Approach:**
- Embedded OpenSCAD viewer
- Real-time updates
- 5th resizable panel

### 3.2 Layout: 5-Panel View
```
┌──────────┬──────────┬──────────┐
│   Top    │   Iso    │          │
├──────────┼──────────┤ OpenSCAD │
│  Front   │   Side   │   3D     │
└──────────┴──────────┴──────────┘
```

## Phase 4: Enhanced UX & Productivity 🚀

### 4.1 Modern UI Framework
- ✅ Tooltips (DONE!)
- Keep Tkinter + CustomTkinter
- Dark mode support

### 4.2 Productivity Features
- ✅ Keyboard shortcuts (partial)
- Command palette (Ctrl+P)
- ✅ Undo/redo (exists, enhance)
- Snapping and guides
- Parametric design
- Assembly constraints

## Phase 5: Integration & Ecosystem 🔗

### 5.1 CAM Integration
- Automatic toolpath generation
- Cut list optimization
- Export to CAM software

### 5.2 Supplier Integration
- API integration with suppliers
- One-click ordering
- Price comparison

### 5.3 Plugin System
- Extensibility for community
- Custom part generators
- Analysis tools

## Phase 6: AI & Automation 🤖

### 6.1 AI-Assisted Design
- Design suggestions
- Part recommendations
- Cost optimization
- Natural language interface

### 6.2 Automated Documentation
- Assembly instructions
- Exploded view diagrams
- Bill of materials with images

## Implementation Priority

### ✅ Completed
- Dynamic panel resizing
- Code refactoring
- JSON parts library format
- Tooltips
- Comprehensive tests
- Complete wireframe files

### 🔄 Current Sprint (Next 1-2 weeks)
1. ✅ **Menu item for JSON export** (DONE!)
2. ✅ **Search and filter in Parts Dialog** (DONE!)
3. ✅ **Hot-reload parts capability** (DONE!)
4. ✅ **Enhanced part metadata** (DONE!)

**🎉 SPRINT COMPLETE! 100% DONE! 🎉**

### 📅 Short-term (3-6 months)
- ✅ **Enhanced BOM with supplier links** (COMPLETE!)
  - ✅ Supplier grouping and subtotals
  - ✅ Sortable columns (click headers)
  - ✅ Search/filter functionality
  - ✅ Expand/collapse all
  - ✅ Copy to clipboard
  - ✅ CSV export
- Three.js 3D viewer integration
- Design gallery website
- Link manager with auto-updates

### 📅 Medium-term (6-12 months)
- Plugin system
- Modern UI (CustomTkinter or PyQt6)
- CAM integration basics
- Mobile companion app

### 📅 Long-term (12+ months)
- AI design assistant
- AR/VR preview
- Collaborative editing
- Marketplace for designs/parts

## Next Immediate Tasks

### Task 1: Search and Filter in Parts Dialog 🎯
**Priority:** HIGH
**Effort:** 2-3 hours
**Impact:** HIGH

Add search box to existing parts dialog:
- Search by name
- Filter by dimensions
- Filter by price range
- Sort by various criteria

### Task 2: Hot-Reload Parts 🎯
**Priority:** MEDIUM
**Effort:** 3-4 hours
**Impact:** MEDIUM

Implement file watching:
- Watch JSON file for changes
- Reload library without restart
- Show notification when updated

### Task 3: Menu Item for JSON Export 🎯
**Priority:** HIGH
**Effort:** 1 hour
**Impact:** HIGH

Add File menu items:
- Export Library to JSON
- Import Library from JSON
- Validate Library

### Task 4: Enhanced Part Metadata 🎯
**Priority:** LOW
**Effort:** 2 hours
**Impact:** LOW

Add to JSON schema:
- Weight calculations
- Part categories/tags
- Custom fields support

## Technical Debt
- ✅ Testing (DONE - 57 tests)
- Documentation (in progress)
- Performance profiling
- Accessibility improvements
- Internationalization

## Community Building
- Discord/Forum
- YouTube tutorials
- Design challenges
- Contributor program
- Documentation sprints
