# Hot Reload Menu Item Update

## Summary
Updated the hot reload feature to:
1. **Default to enabled** - Hot reload is now enabled by default when AlexCAD starts
2. **Dynamic menu label** - The menu item now shows "Enable Hot-Reload" or "Disable Hot-Reload" based on the current state
3. **Auto-initialization** - The library watcher is automatically started at application startup

## Changes Made

### 1. Default State (Line 1427)
```python
hot_reload_enabled = True  # Default enabled
```
Changed from `False` to `True` to enable hot reload by default.

### 2. Menu Item Tracking (Line 1428)
```python
hot_reload_menu_item = None  # Will be set when menu is created
```
Added global variable to track the menu item index for dynamic label updates.

### 3. Dynamic Menu Label (Lines 1677-1679)
```python
# Add hot-reload menu item with dynamic label based on initial state
hot_reload_menu_item = filemenu.index('end') + 1
filemenu.add_command(label="Disable Hot-Reload" if hot_reload_enabled else "Enable Hot-Reload", command=alex_toggle_hot_reload)
```
The menu label now reflects the current state:
- Shows "Disable Hot-Reload" when enabled
- Shows "Enable Hot-Reload" when disabled

### 4. Toggle Function Updates (Lines 1462-1507)
Updated `alex_toggle_hot_reload()` to:
- Include `hot_reload_menu_item` in global variables
- Update menu label when enabling: `filemenu.entryconfig(hot_reload_menu_item, label="Disable Hot-Reload")`
- Update menu label when disabling: `filemenu.entryconfig(hot_reload_menu_item, label="Enable Hot-Reload")`

### 5. Startup Initialization (Lines 1773-1783)
```python
# Initialize hot-reload watcher if enabled by default
if hot_reload_enabled:
    try:
        from packages import library_watcher as lw
        library_watcher = lw.create_library_watcher(
            parts_db.part_libraries_dir,
            on_library_file_changed
        )
    except Exception as e:
        print(f"Warning: Failed to initialize hot-reload watcher: {e}")
        hot_reload_enabled = False
```
Added automatic initialization of the library watcher at startup when hot reload is enabled.

## User Experience
- When AlexCAD starts, hot reload is automatically enabled
- The File menu shows "Disable Hot-Reload" by default
- Clicking the menu item toggles between enabled/disabled states
- The menu label updates immediately to reflect the new state
- Users can easily see the current state at a glance
