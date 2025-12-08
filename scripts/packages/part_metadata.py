"""
Enhanced metadata utilities for AlexCAD parts.

Provides functions for:
- Weight calculations
- Material properties
- Category/tag management
- Custom field handling
"""

# Material densities (g/cm³)
MATERIAL_DENSITIES = {
    "aluminum": 2.7,
    "steel": 7.85,
    "stainless_steel": 7.9,
    "brass": 8.5,
    "copper": 8.96,
    "plastic": 1.2,
    "wood": 0.6,
}

# Standard categories
CATEGORIES = [
    "extrusion",
    "connector",
    "fastener",
    "bracket",
    "plate",
    "custom",
]


def calculate_weight(dim1, dim2, length, material="aluminum"):
    """
    Calculate weight of an extrusion part.
    
    Args:
        dim1: First dimension in mm
        dim2: Second dimension in mm
        length: Length in mm
        material: Material name (default: aluminum)
    
    Returns:
        Weight in kilograms (rounded to 4 decimal places)
    """
    if not length or length <= 0:
        return None
    
    density = MATERIAL_DENSITIES.get(material.lower(), 2.7)
    
    # Volume in mm³
    volume_mm3 = dim1 * dim2 * length
    
    # Convert to cm³
    volume_cm3 = volume_mm3 / 1000
    
    # Weight in grams
    weight_g = volume_cm3 * density
    
    # Convert to kg
    weight_kg = weight_g / 1000
    
    return round(weight_kg, 4)


def auto_categorize(part_name):
    """
    Automatically determine category based on part name.
    
    Args:
        part_name: Name of the part
    
    Returns:
        Category string
    """
    name_lower = part_name.lower()
    
    if "corner" in name_lower or "bracket" in name_lower:
        return "connector"
    elif "plate" in name_lower or "t-plate" in name_lower:
        return "plate"
    elif "bolt" in name_lower or "screw" in name_lower or "nut" in name_lower:
        return "fastener"
    elif "alex" in name_lower or "hfs" in name_lower:
        return "extrusion"
    else:
        return "custom"


def auto_tag(part_name):
    """
    Automatically generate tags based on part name.
    
    Args:
        part_name: Name of the part
    
    Returns:
        List of tag strings
    """
    tags = []
    name_lower = part_name.lower()
    
    # Size tags
    if "2020" in name_lower:
        tags.append("2020")
    if "2040" in name_lower:
        tags.append("2040")
    if "2060" in name_lower:
        tags.append("2060")
    if "2080" in name_lower:
        tags.append("2080")
    if "3030" in name_lower:
        tags.append("3030")
    if "3060" in name_lower:
        tags.append("3060")
    
    # Type tags
    if "corner" in name_lower:
        tags.append("corner")
    if "alex" in name_lower:
        tags.append("profile")
    if "two way" in name_lower or "2-way" in name_lower:
        tags.append("2-way")
    if "three way" in name_lower or "3-way" in name_lower:
        tags.append("3-way")
    
    # Color tags
    if "silver" in name_lower:
        tags.append("silver")
    if "black" in name_lower:
        tags.append("black")
    
    return tags


def format_weight(weight_kg):
    """
    Format weight for display.
    
    Args:
        weight_kg: Weight in kilograms
    
    Returns:
        Formatted string (e.g., "0.5 kg" or "250 g")
    """
    if weight_kg is None:
        return "N/A"
    
    if weight_kg < 0.001:
        return f"{weight_kg * 1000000:.1f} mg"
    elif weight_kg < 1:
        return f"{weight_kg * 1000:.1f} g"
    else:
        return f"{weight_kg:.2f} kg"


def get_material_info(material):
    """
    Get information about a material.
    
    Args:
        material: Material name
    
    Returns:
        Dictionary with material properties
    """
    density = MATERIAL_DENSITIES.get(material.lower(), None)
    
    if density is None:
        return {
            "name": material,
            "density": None,
            "unit": "g/cm³",
            "available": False
        }
    
    return {
        "name": material,
        "density": density,
        "unit": "g/cm³",
        "available": True
    }


# Example usage
if __name__ == "__main__":
    # Calculate weight of a 2020 extrusion, 500mm long
    weight = calculate_weight(20, 20, 500, "aluminum")
    print(f"Weight: {format_weight(weight)}")
    
    # Auto-categorize a part
    category = auto_categorize("2020 Corner Two Way Silver")
    print(f"Category: {category}")
    
    # Auto-tag a part
    tags = auto_tag("2020 Corner Two Way Silver")
    print(f"Tags: {tags}")
    
    # Get material info
    info = get_material_info("aluminum")
    print(f"Material: {info}")
