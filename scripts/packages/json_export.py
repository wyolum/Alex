"""
JSON export and import functionality for Alex CAD parts library.

This module provides functions to:
- Export parts from the database to JSON format
- Import parts from JSON into the database
- Validate JSON structure
- Convert between database and JSON formats
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

from packages import parts_db


def export_library_to_json(library: parts_db.Library, 
                           output_path: str,
                           description: Optional[str] = None) -> Dict[str, Any]:
    """
    Export a parts library to JSON format.
    
    Args:
        library: The Library object to export
        output_path: Path where the JSON file should be saved
        description: Optional description for the library
    
    Returns:
        Dictionary containing the exported data
    """
    # Get all parts from the library
    parts_records = library.part_list()
    
    # Build the parts list
    parts_list = []
    for record in parts_records:
        part_dict = {
            "name": record.Name,
            "wireframe": record.Wireframe,
            "stl_filename": record.STL_filename,
            "url": record.URL,
            "color": record.Color,
            "dimensions": {
                "dim1": record.Dim1,
                "dim2": record.Dim2
            },
            "interfaces": []
        }
        
        # Add interfaces
        for i in range(1, 7):
            interface_name = getattr(record, f"Interface_0{i}")
            if interface_name and interface_name != "NA":
                part_dict["interfaces"].append(interface_name)
        
        # Handle pricing
        if record.Price == "{piecewise}":
            part_dict["price"] = "piecewise"
            part_dict["length"] = None
            
            # Get piecewise pricing data
            piecewise_records = parts_db.piecewise_table.select(
                library.db, 
                where=f'PartName="{record.Name}"'
            )
            
            piecewise_pricing = []
            for pw_record in piecewise_records:
                piecewise_pricing.append({
                    "length_mm": pw_record.Length,
                    "price": pw_record.Price
                })
            
            # Sort by length
            piecewise_pricing.sort(key=lambda x: x["length_mm"])
            part_dict["piecewise_pricing"] = piecewise_pricing
        else:
            # Fixed price
            part_dict["price"] = float(record.Price)
            part_dict["length"] = record.Length
        
        # Enhanced metadata (optional fields with defaults)
        # Material (default: aluminum)
        part_dict["material"] = "aluminum"
        
        # Weight calculation (kg) - aluminum density: 2.7 g/cm³
        # For extrusions: volume = dim1 * dim2 * length (all in mm)
        # Convert to cm³: / 1000, then to grams: * 2.7, then to kg: / 1000
        if part_dict["length"]:
            volume_cm3 = (record.Dim1 * record.Dim2 * part_dict["length"]) / 1000
            weight_kg = (volume_cm3 * 2.7) / 1000
            part_dict["weight_kg"] = round(weight_kg, 4)
        else:
            part_dict["weight_kg"] = None
        
        # Categories and tags
        part_dict["category"] = "extrusion"  # Default category
        part_dict["tags"] = []  # Empty tags by default
        
        # Auto-tag based on name
        name_lower = record.Name.lower()
        if "corner" in name_lower:
            part_dict["tags"].append("corner")
            part_dict["category"] = "connector"
        if "2020" in name_lower:
            part_dict["tags"].append("2020")
        if "3030" in name_lower:
            part_dict["tags"].append("3030")
        if "alex" in name_lower:
            part_dict["tags"].append("profile")
        
        # Custom fields (extensible)
        part_dict["custom_fields"] = {}
        
        parts_list.append(part_dict)
    
    # Build interface definitions
    interface_definitions = {}
    for interface_name, interface_data in parts_db.interface_table.items():
        if interface_data[0] is not None:  # Skip "NA"
            interface_definitions[interface_name] = {
                "hotspot": list(interface_data[0:3]),
                "direction": list(interface_data[3:6])
            }
    
    # Build the complete export structure
    export_data = {
        "library_name": library.name,
        "library_version": "1.0",
        "export_date": datetime.now().strftime("%Y-%m-%d"),
        "description": description or f"Alex CAD Parts Library - {library.name}",
        "parts": parts_list,
        "interface_definitions": interface_definitions
    }
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=4)
    
    return export_data


def import_library_from_json(json_path: str, 
                             target_library: parts_db.Library,
                             overwrite: bool = False,
                             source_library: Optional[parts_db.Library] = None) -> int:
    """
    Import parts from a JSON file into a library.
    
    Args:
        json_path: Path to the JSON file
        target_library: The Library object to import into
        overwrite: If True, overwrite existing parts with the same name
        source_library: Optional source library to copy files from (defaults to Main)
    
    Returns:
        Number of parts imported
    
    Raises:
        ValueError: If JSON structure is invalid
        FileNotFoundError: If JSON file doesn't exist
    """
    import shutil
    
    # Load JSON
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Validate structure
    validate_json_structure(data)
    
    # Use Main library as source if not specified
    if source_library is None:
        source_library = parts_db.Main
    
    parts_imported = 0
    
    for part_data in data["parts"]:
        # Check if part already exists
        existing = parts_db.part_table.select(
            target_library.db,
            where=f'Name="{part_data["name"]}"'
        )
        
        if existing and not overwrite:
            print(f"Skipping {part_data['name']} - already exists")
            continue
        
        # Delete existing if overwriting
        if existing and overwrite:
            parts_db.part_table.delete(
                target_library.db,
                where=f'Name="{part_data["name"]}"'
            )
        
        # Prepare part values for database
        values = [
            part_data["name"],
            part_data["wireframe"],
            part_data["stl_filename"],
            part_data["price"] if isinstance(part_data["price"], (int, float)) else "{piecewise}",
            part_data["url"],
            part_data["color"],
            part_data["length"] if part_data["length"] is not None else "NA",
            part_data["dimensions"]["dim1"],
            part_data["dimensions"]["dim2"]
        ]
        
        # Add interfaces (pad to 6)
        interfaces = part_data.get("interfaces", [])
        values.extend(interfaces)
        values.extend(["NA"] * (6 - len(interfaces)))
        
        # Insert part
        parts_db.part_table.insert(target_library.db, [values])
        
        # Handle piecewise pricing
        if part_data["price"] == "piecewise":
            # Delete existing piecewise data
            parts_db.piecewise_table.delete(
                target_library.db,
                where=f'PartName="{part_data["name"]}"'
            )
            
            # Insert new piecewise data
            piecewise_values = [
                (part_data["name"], tier["length_mm"], tier["price"])
                for tier in part_data["piecewise_pricing"]
            ]
            parts_db.piecewise_table.insert(target_library.db, piecewise_values)
        
        # Copy STL file if it exists
        if part_data["stl_filename"]:
            source_stl = os.path.join(source_library.stl_dir, part_data["stl_filename"])
            target_stl = os.path.join(target_library.stl_dir, part_data["stl_filename"])
            
            if os.path.exists(source_stl) and not os.path.exists(target_stl):
                try:
                    shutil.copy2(source_stl, target_stl)
                    print(f"Copied STL: {part_data['stl_filename']}")
                except Exception as e:
                    print(f"Warning: Could not copy STL {part_data['stl_filename']}: {e}")
        
        # Copy thumbnail if it exists
        thumbnail_name = part_data["name"].replace(" ", "") + ".png"
        source_thumb = os.path.join(source_library.thumbnail_dir, thumbnail_name)
        target_thumb = os.path.join(target_library.thumbnail_dir, thumbnail_name)
        
        if os.path.exists(source_thumb) and not os.path.exists(target_thumb):
            try:
                shutil.copy2(source_thumb, target_thumb)
                print(f"Copied thumbnail: {thumbnail_name}")
            except Exception as e:
                print(f"Warning: Could not copy thumbnail {thumbnail_name}: {e}")
        
        # Copy wireframe if it's a custom one
        wireframe_name = part_data["wireframe"] + ".npy"
        source_wf = os.path.join(source_library.wireframe_dir, wireframe_name)
        target_wf = os.path.join(target_library.wireframe_dir, wireframe_name)
        
        if os.path.exists(source_wf) and not os.path.exists(target_wf):
            try:
                shutil.copy2(source_wf, target_wf)
                print(f"Copied wireframe: {wireframe_name}")
            except Exception as e:
                print(f"Warning: Could not copy wireframe {wireframe_name}: {e}")
        
        parts_imported += 1
    
    return parts_imported


def validate_json_structure(data: Dict[str, Any]) -> bool:
    """
    Validate that a JSON structure conforms to the expected format.
    
    Args:
        data: Dictionary loaded from JSON
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If structure is invalid
    """
    # Check top-level keys
    required_keys = ["library_name", "library_version", "export_date", 
                    "description", "parts", "interface_definitions"]
    
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")
    
    # Validate parts
    if not isinstance(data["parts"], list):
        raise ValueError("'parts' must be a list")
    
    for i, part in enumerate(data["parts"]):
        validate_part_structure(part, i)
    
    # Validate interface definitions
    if not isinstance(data["interface_definitions"], dict):
        raise ValueError("'interface_definitions' must be a dictionary")
    
    for name, interface in data["interface_definitions"].items():
        validate_interface_structure(interface, name)
    
    return True


def validate_part_structure(part: Dict[str, Any], index: int = 0) -> bool:
    """
    Validate a single part's structure.
    
    Args:
        part: Part dictionary
        index: Index of part in list (for error messages)
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If structure is invalid
    """
    required_fields = ["name", "wireframe", "stl_filename", "price", 
                      "url", "color", "length", "dimensions", "interfaces"]
    
    for field in required_fields:
        if field not in part:
            raise ValueError(f"Part {index} missing required field: {field}")
    
    # Validate dimensions
    if not isinstance(part["dimensions"], dict):
        raise ValueError(f"Part {index}: dimensions must be a dictionary")
    
    if "dim1" not in part["dimensions"] or "dim2" not in part["dimensions"]:
        raise ValueError(f"Part {index}: dimensions must have dim1 and dim2")
    
    # Validate interfaces
    if not isinstance(part["interfaces"], list):
        raise ValueError(f"Part {index}: interfaces must be a list")
    
    # Validate piecewise pricing if applicable
    if part["price"] == "piecewise":
        if "piecewise_pricing" not in part:
            raise ValueError(f"Part {index}: piecewise parts must have piecewise_pricing")
        
        if not isinstance(part["piecewise_pricing"], list):
            raise ValueError(f"Part {index}: piecewise_pricing must be a list")
        
        for tier in part["piecewise_pricing"]:
            if "length_mm" not in tier or "price" not in tier:
                raise ValueError(f"Part {index}: piecewise tier missing length_mm or price")
    
    return True


def validate_interface_structure(interface: Dict[str, Any], name: str) -> bool:
    """
    Validate an interface definition's structure.
    
    Args:
        interface: Interface dictionary
        name: Name of interface (for error messages)
    
    Returns:
        True if valid
    
    Raises:
        ValueError: If structure is invalid
    """
    if "hotspot" not in interface:
        raise ValueError(f"Interface {name}: missing hotspot")
    
    if "direction" not in interface:
        raise ValueError(f"Interface {name}: missing direction")
    
    if not isinstance(interface["hotspot"], list) or len(interface["hotspot"]) != 3:
        raise ValueError(f"Interface {name}: hotspot must be a list of 3 numbers")
    
    if not isinstance(interface["direction"], list) or len(interface["direction"]) != 3:
        raise ValueError(f"Interface {name}: direction must be a list of 3 numbers")
    
    return True


def get_part_by_name(json_path: str, part_name: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific part from a JSON file by name.
    
    Args:
        json_path: Path to the JSON file
        part_name: Name of the part to retrieve
    
    Returns:
        Part dictionary if found, None otherwise
    """
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    for part in data["parts"]:
        if part["name"] == part_name:
            return part
    
    return None


def calculate_piecewise_price(part_data: Dict[str, Any], length_mm: float) -> float:
    """
    Calculate the price for a piecewise-priced part at a given length.
    
    Args:
        part_data: Part dictionary from JSON
        length_mm: Length in millimeters
    
    Returns:
        Calculated price
    
    Raises:
        ValueError: If part doesn't have piecewise pricing or length is invalid
    """
    if part_data["price"] != "piecewise":
        raise ValueError(f"Part {part_data['name']} does not have piecewise pricing")
    
    if length_mm <= 0:
        raise ValueError("Length must be positive")
    
    pricing = part_data["piecewise_pricing"]
    
    # Find the appropriate tier
    for i, tier in enumerate(pricing):
        if length_mm <= tier["length_mm"]:
            if i == 0:
                # First tier - use its price
                return tier["price"]
            else:
                # Interpolate between previous and current tier
                prev_tier = pricing[i - 1]
                length_range = tier["length_mm"] - prev_tier["length_mm"]
                price_range = tier["price"] - prev_tier["price"]
                length_offset = length_mm - prev_tier["length_mm"]
                
                return prev_tier["price"] + (price_range * length_offset / length_range)
    
    # Beyond last tier - extrapolate
    last_tier = pricing[-1]
    if len(pricing) > 1:
        prev_tier = pricing[-2]
        length_range = last_tier["length_mm"] - prev_tier["length_mm"]
        price_range = last_tier["price"] - prev_tier["price"]
        length_offset = length_mm - last_tier["length_mm"]
        
        return last_tier["price"] + (price_range * length_offset / length_range)
    else:
        # Only one tier - use its price
        return last_tier["price"]
