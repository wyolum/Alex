"""
Unit tests for JSON export/import functionality.

This module tests the json_export module functions.
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add the scripts directory to the path
project_root = Path(__file__).parent.parent
scripts_dir = project_root / "scripts"
sys.path.insert(0, str(scripts_dir))

from packages import parts_db
from packages import json_export


class TestJSONExport(unittest.TestCase):
    """Test JSON export functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.main_lib = parts_db.Main
        self.temp_dir = tempfile.mkdtemp()
        self.json_path = os.path.join(self.temp_dir, "test_export.json")
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_export_library_creates_file(self):
        """Test that export creates a JSON file."""
        json_export.export_library_to_json(self.main_lib, self.json_path)
        self.assertTrue(os.path.exists(self.json_path), "Export should create a file")
    
    def test_export_library_valid_json(self):
        """Test that exported file is valid JSON."""
        json_export.export_library_to_json(self.main_lib, self.json_path)
        
        with open(self.json_path, 'r') as f:
            data = json.load(f)
        
        self.assertIsInstance(data, dict, "Exported data should be a dictionary")
    
    def test_export_library_has_required_keys(self):
        """Test that exported JSON has all required keys."""
        json_export.export_library_to_json(self.main_lib, self.json_path)
        
        with open(self.json_path, 'r') as f:
            data = json.load(f)
        
        required_keys = ["library_name", "library_version", "export_date", 
                        "description", "parts", "interface_definitions"]
        
        for key in required_keys:
            self.assertIn(key, data, f"Export should have '{key}' key")
    
    def test_export_library_name(self):
        """Test that library name is correctly exported."""
        json_export.export_library_to_json(self.main_lib, self.json_path)
        
        with open(self.json_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["library_name"], "Main")
    
    def test_export_parts_count(self):
        """Test that all parts are exported."""
        json_export.export_library_to_json(self.main_lib, self.json_path)
        
        with open(self.json_path, 'r') as f:
            data = json.load(f)
        
        db_parts = self.main_lib.part_list()
        self.assertEqual(len(data["parts"]), len(db_parts), 
                        "Should export all parts")
    
    def test_export_with_custom_description(self):
        """Test export with custom description."""
        custom_desc = "Custom test description"
        json_export.export_library_to_json(self.main_lib, self.json_path, 
                                          description=custom_desc)
        
        with open(self.json_path, 'r') as f:
            data = json.load(f)
        
        self.assertEqual(data["description"], custom_desc)


class TestJSONValidation(unittest.TestCase):
    """Test JSON validation functions."""
    
    def test_validate_valid_structure(self):
        """Test validation of a valid structure."""
        json_path = project_root / "part_libraries" / "parts_library.json"
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Should not raise an exception
        result = json_export.validate_json_structure(data)
        self.assertTrue(result)
    
    def test_validate_missing_key(self):
        """Test validation fails with missing key."""
        invalid_data = {
            "library_name": "Test",
            "parts": []
            # Missing other required keys
        }
        
        with self.assertRaises(ValueError) as context:
            json_export.validate_json_structure(invalid_data)
        
        self.assertIn("Missing required key", str(context.exception))
    
    def test_validate_invalid_parts_type(self):
        """Test validation fails when parts is not a list."""
        invalid_data = {
            "library_name": "Test",
            "library_version": "1.0",
            "export_date": "2025-12-07",
            "description": "Test",
            "parts": "not a list",  # Invalid
            "interface_definitions": {}
        }
        
        with self.assertRaises(ValueError) as context:
            json_export.validate_json_structure(invalid_data)
        
        self.assertIn("parts", str(context.exception).lower())
    
    def test_validate_part_missing_field(self):
        """Test validation fails when part is missing required field."""
        invalid_part = {
            "name": "Test Part",
            "wireframe": "Cube"
            # Missing other required fields
        }
        
        with self.assertRaises(ValueError) as context:
            json_export.validate_part_structure(invalid_part, 0)
        
        self.assertIn("missing required field", str(context.exception).lower())
    
    def test_validate_part_invalid_dimensions(self):
        """Test validation fails with invalid dimensions."""
        invalid_part = {
            "name": "Test Part",
            "wireframe": "Cube",
            "stl_filename": "test.stl",
            "price": 10.0,
            "url": "http://example.com",
            "color": "red",
            "length": 100,
            "dimensions": "not a dict",  # Invalid
            "interfaces": []
        }
        
        with self.assertRaises(ValueError) as context:
            json_export.validate_part_structure(invalid_part, 0)
        
        self.assertIn("dimensions", str(context.exception).lower())
    
    def test_validate_piecewise_missing_pricing(self):
        """Test validation fails when piecewise part missing pricing data."""
        invalid_part = {
            "name": "Test Part",
            "wireframe": "Cube",
            "stl_filename": "test.stl",
            "price": "piecewise",  # But no piecewise_pricing
            "url": "http://example.com",
            "color": "red",
            "length": None,
            "dimensions": {"dim1": 20, "dim2": 20},
            "interfaces": []
        }
        
        with self.assertRaises(ValueError) as context:
            json_export.validate_part_structure(invalid_part, 0)
        
        self.assertIn("piecewise_pricing", str(context.exception).lower())
    
    def test_validate_interface_missing_hotspot(self):
        """Test validation fails when interface missing hotspot."""
        invalid_interface = {
            "direction": [1, 0, 0]
            # Missing hotspot
        }
        
        with self.assertRaises(ValueError) as context:
            json_export.validate_interface_structure(invalid_interface, "test")
        
        self.assertIn("hotspot", str(context.exception).lower())
    
    def test_validate_interface_invalid_direction(self):
        """Test validation fails with invalid direction."""
        invalid_interface = {
            "hotspot": [0, 0, 0],
            "direction": [1, 0]  # Should have 3 components
        }
        
        with self.assertRaises(ValueError) as context:
            json_export.validate_interface_structure(invalid_interface, "test")
        
        self.assertIn("direction", str(context.exception).lower())


class TestGetPartByName(unittest.TestCase):
    """Test getting parts by name from JSON."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.json_path = project_root / "part_libraries" / "parts_library.json"
    
    def test_get_existing_part(self):
        """Test getting an existing part."""
        part = json_export.get_part_by_name(str(self.json_path), 
                                           "2020 Corner Three Way Silver")
        
        self.assertIsNotNone(part, "Should find existing part")
        self.assertEqual(part["name"], "2020 Corner Three Way Silver")
    
    def test_get_nonexistent_part(self):
        """Test getting a non-existent part."""
        part = json_export.get_part_by_name(str(self.json_path), 
                                           "Nonexistent Part")
        
        self.assertIsNone(part, "Should return None for non-existent part")
    
    def test_get_part_has_correct_structure(self):
        """Test that retrieved part has correct structure."""
        part = json_export.get_part_by_name(str(self.json_path), 
                                           "2020 Corner Three Way Silver")
        
        self.assertIn("name", part)
        self.assertIn("price", part)
        self.assertIn("dimensions", part)
        self.assertIn("interfaces", part)


class TestPiecewisePriceCalculation(unittest.TestCase):
    """Test piecewise price calculation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.json_path = project_root / "part_libraries" / "parts_library.json"
        self.piecewise_part = json_export.get_part_by_name(
            str(self.json_path), "2020 HFS5"
        )
    
    def test_calculate_price_at_tier_boundary(self):
        """Test price calculation at tier boundary."""
        # At 50mm, price should be 3.18
        price = json_export.calculate_piecewise_price(self.piecewise_part, 50)
        self.assertAlmostEqual(price, 3.18, places=2)
    
    def test_calculate_price_between_tiers(self):
        """Test price calculation between tiers."""
        # Between 50mm and 299mm, should interpolate
        price = json_export.calculate_piecewise_price(self.piecewise_part, 150)
        self.assertIsInstance(price, float)
        self.assertGreater(price, 0)
    
    def test_calculate_price_invalid_length(self):
        """Test that invalid length raises error."""
        with self.assertRaises(ValueError):
            json_export.calculate_piecewise_price(self.piecewise_part, 0)
        
        with self.assertRaises(ValueError):
            json_export.calculate_piecewise_price(self.piecewise_part, -10)
    
    def test_calculate_price_non_piecewise_part(self):
        """Test that non-piecewise part raises error."""
        fixed_part = json_export.get_part_by_name(
            str(self.json_path), "2020 Corner Three Way Silver"
        )
        
        with self.assertRaises(ValueError) as context:
            json_export.calculate_piecewise_price(fixed_part, 100)
        
        self.assertIn("does not have piecewise pricing", str(context.exception))
    
    def test_calculate_price_beyond_last_tier(self):
        """Test price calculation beyond last tier (extrapolation)."""
        # Beyond 4000mm
        price = json_export.calculate_piecewise_price(self.piecewise_part, 5000)
        self.assertIsInstance(price, float)
        self.assertGreater(price, 26.4)  # Should be more than the last tier price
    
    def test_calculate_price_various_lengths(self):
        """Test price calculation at various lengths."""
        # Test at specific points
        lengths = [100, 200, 300, 400, 500]
        prices = [json_export.calculate_piecewise_price(self.piecewise_part, l) 
                 for l in lengths]
        
        # All prices should be positive
        for price in prices:
            self.assertGreater(price, 0, "All prices should be positive")


class TestJSONImport(unittest.TestCase):
    """Test JSON import functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        import uuid
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test library with unique name to avoid conflicts
        self.test_lib_name = f"TestImportLib_{uuid.uuid4().hex[:8]}"
        self.test_lib = parts_db.Library(self.test_lib_name)
        
        # Create a minimal test JSON
        self.test_json_path = os.path.join(self.temp_dir, "test_import.json")
        self.test_data = {
            "library_name": "Test",
            "library_version": "1.0",
            "export_date": "2025-12-07",
            "description": "Test library",
            "parts": [
                {
                    "name": "Test Part 1",
                    "wireframe": "Cube",
                    "stl_filename": "test1.stl",
                    "price": 10.5,
                    "url": "http://example.com",
                    "color": "red",
                    "length": 100,
                    "dimensions": {"dim1": 20, "dim2": 20},
                    "interfaces": ["2020+X", "2020-Z"]
                }
            ],
            "interface_definitions": {
                "2020+X": {
                    "hotspot": [15, 0, 15],
                    "direction": [1, 0, 0]
                },
                "2020-Z": {
                    "hotspot": [0, 0, 0],
                    "direction": [0, 0, -1]
                }
            }
        }
        
        with open(self.test_json_path, 'w') as f:
            json.dump(self.test_data, f)
    
    def tearDown(self):
        """Clean up test files."""
        import shutil
        
        # Clean up temp directory
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Clean up test library - be more aggressive
        if hasattr(self, 'test_lib_name'):
            test_lib_dir = os.path.join(parts_db.part_libraries_dir, self.test_lib_name)
            if os.path.exists(test_lib_dir):
                # Close any database connections
                if hasattr(self, 'test_lib') and hasattr(self.test_lib, 'db'):
                    try:
                        self.test_lib.db.commit()
                    except:
                        pass
                # Remove the directory
                shutil.rmtree(test_lib_dir)
    
    def test_import_creates_parts(self):
        """Test that import creates parts in the library."""
        # Library starts with 1 Example Part
        initial_count = len(self.test_lib.part_list())
        
        count = json_export.import_library_from_json(
            self.test_json_path, self.test_lib
        )
        
        self.assertEqual(count, 1, "Should import 1 part")
        
        parts = self.test_lib.part_list()
        self.assertEqual(len(parts), initial_count + 1, 
                        f"Library should have {initial_count + 1} parts (Example Part + imported)")
    
    def test_import_part_data_correct(self):
        """Test that imported part data is correct."""
        json_export.import_library_from_json(self.test_json_path, self.test_lib)
        
        # Find the imported part by name
        parts = self.test_lib.part_list()
        part = None
        for p in parts:
            if p.Name == "Test Part 1":
                part = p
                break
        
        self.assertIsNotNone(part, "Should find imported part")
        self.assertEqual(part.Name, "Test Part 1")
        self.assertEqual(part.Dim1, 20)
        self.assertEqual(part.Dim2, 20)
        self.assertEqual(part.Wireframe, "Cube")
    
    def test_import_skip_existing(self):
        """Test that import skips existing parts by default."""
        # Import once
        count1 = json_export.import_library_from_json(
            self.test_json_path, self.test_lib
        )
        
        # Import again (should skip)
        count2 = json_export.import_library_from_json(
            self.test_json_path, self.test_lib
        )
        
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 0, "Should skip existing part")
    
    def test_import_overwrite_existing(self):
        """Test that import can overwrite existing parts."""
        # Import once
        json_export.import_library_from_json(self.test_json_path, self.test_lib)
        
        # Modify the JSON
        self.test_data["parts"][0]["price"] = 20.0
        with open(self.test_json_path, 'w') as f:
            json.dump(self.test_data, f)
        
        # Import again with overwrite
        count = json_export.import_library_from_json(
            self.test_json_path, self.test_lib, overwrite=True
        )
        
        self.assertEqual(count, 1, "Should import 1 part")
        
        # Verify price was updated - find the imported part by name
        parts = self.test_lib.part_list()
        imported_part = None
        for p in parts:
            if p.Name == "Test Part 1":
                imported_part = p
                break
        
        self.assertIsNotNone(imported_part, "Should find imported part")
        self.assertEqual(float(imported_part.Price), 20.0)
    
    def test_import_invalid_json_raises_error(self):
        """Test that importing invalid JSON raises error."""
        invalid_json_path = os.path.join(self.temp_dir, "invalid.json")
        
        with open(invalid_json_path, 'w') as f:
            json.dump({"invalid": "structure"}, f)
        
        with self.assertRaises(ValueError):
            json_export.import_library_from_json(invalid_json_path, self.test_lib)


if __name__ == '__main__':
    unittest.main()
