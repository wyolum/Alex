"""
Unit tests for JSON parts library functionality.

This module tests:
1. JSON file structure and validity
2. Part data integrity
3. Piecewise pricing data
4. Interface definitions
5. Data consistency with the database
"""

import json
import os
import sys
import unittest
from pathlib import Path

# Add the scripts directory to the path
project_root = Path(__file__).parent.parent
scripts_dir = project_root / "scripts"
sys.path.insert(0, str(scripts_dir))

from packages import parts_db


class TestJSONStructure(unittest.TestCase):
    """Test the basic structure of the JSON file."""
    
    @classmethod
    def setUpClass(cls):
        """Load the JSON file once for all tests."""
        json_path = project_root / "part_libraries" / "parts_library.json"
        with open(json_path, 'r') as f:
            cls.data = json.load(f)
    
    def test_json_file_exists(self):
        """Test that the JSON file exists."""
        json_path = project_root / "part_libraries" / "parts_library.json"
        self.assertTrue(json_path.exists(), "JSON file should exist")
    
    def test_json_is_valid(self):
        """Test that the JSON file is valid and can be parsed."""
        self.assertIsNotNone(self.data, "JSON should be parseable")
        self.assertIsInstance(self.data, dict, "JSON root should be a dictionary")
    
    def test_has_required_top_level_keys(self):
        """Test that all required top-level keys are present."""
        required_keys = ["library_name", "library_version", "export_date", 
                        "description", "parts", "interface_definitions"]
        for key in required_keys:
            self.assertIn(key, self.data, f"JSON should have '{key}' key")
    
    def test_library_metadata(self):
        """Test library metadata fields."""
        self.assertEqual(self.data["library_name"], "Main")
        self.assertIsInstance(self.data["library_version"], str)
        self.assertIsInstance(self.data["export_date"], str)
        self.assertIsInstance(self.data["description"], str)
    
    def test_parts_is_list(self):
        """Test that parts is a list."""
        self.assertIsInstance(self.data["parts"], list, "Parts should be a list")
        self.assertGreater(len(self.data["parts"]), 0, "Parts list should not be empty")
    
    def test_interface_definitions_is_dict(self):
        """Test that interface_definitions is a dictionary."""
        self.assertIsInstance(self.data["interface_definitions"], dict, 
                            "Interface definitions should be a dictionary")


class TestPartData(unittest.TestCase):
    """Test individual part data structure and validity."""
    
    @classmethod
    def setUpClass(cls):
        """Load the JSON file once for all tests."""
        json_path = project_root / "part_libraries" / "parts_library.json"
        with open(json_path, 'r') as f:
            cls.data = json.load(f)
        cls.parts = cls.data["parts"]
    
    def test_part_count(self):
        """Test that we have the expected number of parts."""
        # According to BRANCH_README.md, there should be 15 parts
        self.assertEqual(len(self.parts), 15, "Should have 15 parts")
    
    def test_all_parts_have_required_fields(self):
        """Test that all parts have required fields."""
        required_fields = ["name", "wireframe", "stl_filename", "price", 
                          "url", "color", "length", "dimensions", "interfaces"]
        
        for i, part in enumerate(self.parts):
            with self.subTest(part_index=i, part_name=part.get("name", "unknown")):
                for field in required_fields:
                    self.assertIn(field, part, 
                                f"Part {i} should have '{field}' field")
    
    def test_part_names_are_unique(self):
        """Test that all part names are unique."""
        names = [part["name"] for part in self.parts]
        self.assertEqual(len(names), len(set(names)), 
                        "All part names should be unique")
    
    def test_part_names_are_strings(self):
        """Test that all part names are non-empty strings."""
        for part in self.parts:
            self.assertIsInstance(part["name"], str)
            self.assertGreater(len(part["name"]), 0)
    
    def test_dimensions_structure(self):
        """Test that dimensions have the correct structure."""
        for part in self.parts:
            dims = part["dimensions"]
            self.assertIsInstance(dims, dict, "Dimensions should be a dict")
            self.assertIn("dim1", dims, "Dimensions should have dim1")
            self.assertIn("dim2", dims, "Dimensions should have dim2")
            self.assertIsInstance(dims["dim1"], int, "dim1 should be an integer")
            self.assertIsInstance(dims["dim2"], int, "dim2 should be an integer")
            self.assertGreater(dims["dim1"], 0, "dim1 should be positive")
            self.assertGreater(dims["dim2"], 0, "dim2 should be positive")
    
    def test_interfaces_is_list(self):
        """Test that interfaces is a list."""
        for part in self.parts:
            self.assertIsInstance(part["interfaces"], list, 
                                "Interfaces should be a list")
    
    def test_stl_filename_format(self):
        """Test that STL filenames have .stl extension."""
        for part in self.parts:
            stl = part["stl_filename"]
            self.assertIsInstance(stl, str)
            self.assertTrue(stl.endswith(".stl"), 
                          f"STL filename should end with .stl: {stl}")
    
    def test_url_format(self):
        """Test that URLs are valid strings."""
        for part in self.parts:
            url = part["url"]
            self.assertIsInstance(url, str)
            self.assertTrue(url.startswith("http"), 
                          f"URL should start with http: {url}")
    
    def test_color_format(self):
        """Test that colors are valid strings."""
        for part in self.parts:
            color = part["color"]
            self.assertIsInstance(color, str)
            self.assertGreater(len(color), 0, "Color should not be empty")


class TestPricingData(unittest.TestCase):
    """Test pricing data including piecewise pricing."""
    
    @classmethod
    def setUpClass(cls):
        """Load the JSON file once for all tests."""
        json_path = project_root / "part_libraries" / "parts_library.json"
        with open(json_path, 'r') as f:
            cls.data = json.load(f)
        cls.parts = cls.data["parts"]
    
    def test_fixed_price_parts(self):
        """Test parts with fixed prices."""
        fixed_price_parts = [p for p in self.parts 
                            if isinstance(p["price"], (int, float))]
        
        # According to BRANCH_README.md, there should be 8 fixed-price parts
        self.assertEqual(len(fixed_price_parts), 8, 
                        "Should have 8 fixed-price parts")
        
        for part in fixed_price_parts:
            self.assertGreater(part["price"], 0, 
                             f"Price should be positive for {part['name']}")
            # Fixed price parts should have a specific length
            self.assertIsInstance(part["length"], int, 
                                f"Fixed price part should have integer length: {part['name']}")
            self.assertGreater(part["length"], 0)
    
    def test_piecewise_price_parts(self):
        """Test parts with piecewise pricing."""
        piecewise_parts = [p for p in self.parts if p["price"] == "piecewise"]
        
        # According to BRANCH_README.md, there should be 7 piecewise parts
        self.assertEqual(len(piecewise_parts), 7, 
                        "Should have 7 piecewise pricing parts")
        
        for part in piecewise_parts:
            with self.subTest(part_name=part["name"]):
                # Piecewise parts should have null length
                self.assertIsNone(part["length"], 
                                f"Piecewise part should have null length: {part['name']}")
                
                # Should have piecewise_pricing field
                self.assertIn("piecewise_pricing", part, 
                            f"Piecewise part should have piecewise_pricing: {part['name']}")
                
                pricing = part["piecewise_pricing"]
                self.assertIsInstance(pricing, list, "Piecewise pricing should be a list")
                self.assertGreater(len(pricing), 0, "Piecewise pricing should not be empty")
    
    def test_piecewise_pricing_structure(self):
        """Test the structure of piecewise pricing data."""
        piecewise_parts = [p for p in self.parts if p["price"] == "piecewise"]
        
        for part in piecewise_parts:
            pricing = part["piecewise_pricing"]
            
            for i, tier in enumerate(pricing):
                with self.subTest(part_name=part["name"], tier_index=i):
                    self.assertIn("length_mm", tier, "Tier should have length_mm")
                    self.assertIn("price", tier, "Tier should have price")
                    
                    self.assertIsInstance(tier["length_mm"], int, 
                                        "length_mm should be an integer")
                    self.assertIsInstance(tier["price"], (int, float), 
                                        "price should be a number")
                    
                    self.assertGreater(tier["length_mm"], 0, 
                                     "length_mm should be positive")
                    self.assertGreater(tier["price"], 0, 
                                     "price should be positive")
    
    def test_piecewise_pricing_sorted(self):
        """Test that piecewise pricing tiers are sorted by length."""
        piecewise_parts = [p for p in self.parts if p["price"] == "piecewise"]
        
        for part in piecewise_parts:
            pricing = part["piecewise_pricing"]
            lengths = [tier["length_mm"] for tier in pricing]
            
            with self.subTest(part_name=part["name"]):
                self.assertEqual(lengths, sorted(lengths), 
                               f"Pricing tiers should be sorted by length for {part['name']}")


class TestInterfaceDefinitions(unittest.TestCase):
    """Test interface definitions."""
    
    @classmethod
    def setUpClass(cls):
        """Load the JSON file once for all tests."""
        json_path = project_root / "part_libraries" / "parts_library.json"
        with open(json_path, 'r') as f:
            cls.data = json.load(f)
        cls.interfaces = cls.data["interface_definitions"]
    
    def test_interface_definitions_exist(self):
        """Test that interface definitions exist."""
        self.assertGreater(len(self.interfaces), 0, 
                          "Should have interface definitions")
    
    def test_interface_structure(self):
        """Test that each interface has required fields."""
        for name, interface in self.interfaces.items():
            with self.subTest(interface_name=name):
                self.assertIn("hotspot", interface, 
                            f"Interface {name} should have hotspot")
                self.assertIn("direction", interface, 
                            f"Interface {name} should have direction")
                
                # Test hotspot
                hotspot = interface["hotspot"]
                self.assertIsInstance(hotspot, list, "Hotspot should be a list")
                self.assertEqual(len(hotspot), 3, "Hotspot should have 3 coordinates")
                for coord in hotspot:
                    self.assertIsInstance(coord, (int, float), 
                                        "Hotspot coordinates should be numbers")
                
                # Test direction
                direction = interface["direction"]
                self.assertIsInstance(direction, list, "Direction should be a list")
                self.assertEqual(len(direction), 3, "Direction should have 3 components")
                for comp in direction:
                    self.assertIsInstance(comp, (int, float), 
                                        "Direction components should be numbers")
                    self.assertIn(comp, [-1, 0, 1], 
                                "Direction components should be -1, 0, or 1")
    
    def test_direction_is_unit_vector(self):
        """Test that direction vectors are unit vectors."""
        for name, interface in self.interfaces.items():
            direction = interface["direction"]
            magnitude_squared = sum(d**2 for d in direction)
            
            with self.subTest(interface_name=name):
                self.assertAlmostEqual(magnitude_squared, 1.0, places=5,
                                     msg=f"Direction should be a unit vector for {name}")
    
    def test_referenced_interfaces_are_defined(self):
        """Test that all interfaces referenced by parts are defined."""
        parts = self.data["parts"]
        
        for part in parts:
            for interface_name in part["interfaces"]:
                with self.subTest(part_name=part["name"], 
                                interface_name=interface_name):
                    self.assertIn(interface_name, self.interfaces, 
                                f"Interface {interface_name} should be defined")


class TestDataConsistency(unittest.TestCase):
    """Test consistency between JSON and database."""
    
    @classmethod
    def setUpClass(cls):
        """Load the JSON file and database."""
        json_path = project_root / "part_libraries" / "parts_library.json"
        with open(json_path, 'r') as f:
            cls.json_data = json.load(f)
        
        # Load the Main library from the database
        cls.main_lib = parts_db.Main
    
    def test_library_exists(self):
        """Test that the Main library exists."""
        self.assertIsNotNone(self.main_lib, "Main library should exist")
    
    def test_part_count_matches(self):
        """Test that JSON and database have the same number of parts."""
        json_parts = self.json_data["parts"]
        db_parts = self.main_lib.part_list()
        
        self.assertEqual(len(json_parts), len(db_parts), 
                        "JSON and database should have the same number of parts")
    
    def test_part_names_match(self):
        """Test that all JSON part names exist in the database."""
        json_names = {part["name"] for part in self.json_data["parts"]}
        db_parts = self.main_lib.part_list()
        db_names = {part.Name for part in db_parts}
        
        self.assertEqual(json_names, db_names, 
                        "JSON and database should have the same part names")
    
    def test_part_data_consistency(self):
        """Test that part data is consistent between JSON and database."""
        json_parts = {part["name"]: part for part in self.json_data["parts"]}
        db_parts = {part.Name: part for part in self.main_lib.part_list()}
        
        for name in json_parts.keys():
            with self.subTest(part_name=name):
                json_part = json_parts[name]
                db_part = db_parts[name]
                
                # Test dimensions
                self.assertEqual(json_part["dimensions"]["dim1"], db_part.Dim1,
                               f"dim1 should match for {name}")
                self.assertEqual(json_part["dimensions"]["dim2"], db_part.Dim2,
                               f"dim2 should match for {name}")
                
                # Test wireframe
                self.assertEqual(json_part["wireframe"], db_part.Wireframe,
                               f"wireframe should match for {name}")
                
                # Test STL filename
                self.assertEqual(json_part["stl_filename"], db_part.STL_filename,
                               f"STL filename should match for {name}")
                
                # Test URL
                self.assertEqual(json_part["url"], db_part.URL,
                               f"URL should match for {name}")
                
                # Test color
                self.assertEqual(json_part["color"], db_part.Color,
                               f"Color should match for {name}")


class TestJSONExportImport(unittest.TestCase):
    """Test JSON export and import functionality."""
    
    def test_json_roundtrip(self):
        """Test that JSON can be exported and re-imported."""
        json_path = project_root / "part_libraries" / "parts_library.json"
        
        # Load the JSON
        with open(json_path, 'r') as f:
            original_data = json.load(f)
        
        # Export to string and re-import
        json_string = json.dumps(original_data, indent=4)
        reimported_data = json.loads(json_string)
        
        # Compare
        self.assertEqual(original_data, reimported_data, 
                        "JSON should survive roundtrip")
    
    def test_json_formatting(self):
        """Test that JSON is properly formatted."""
        json_path = project_root / "part_libraries" / "parts_library.json"
        
        with open(json_path, 'r') as f:
            content = f.read()
        
        # Test that it's indented (has multiple spaces)
        self.assertIn("    ", content, "JSON should be indented")
        
        # Test that it can be parsed
        data = json.loads(content)
        self.assertIsNotNone(data)


if __name__ == '__main__':
    unittest.main()
