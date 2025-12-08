#!/usr/bin/env python3
"""
Test runner script for JSON functionality tests.

This script runs all JSON-related tests and provides a summary.
"""

import sys
import subprocess
import os

def run_tests(verbose=True, coverage=False):
    """
    Run the JSON functionality tests.
    
    Args:
        verbose: If True, show detailed test output
        coverage: If True, generate coverage report
    """
    # Ensure we're in the project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    print("=" * 70)
    print("JSON Functionality Test Runner")
    print("=" * 70)
    print()
    
    # Build pytest command
    cmd = ["python", "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=scripts/packages", "--cov-report=term", "--cov-report=html"])
    
    # Add color output
    cmd.append("--color=yes")
    
    # Run tests
    print(f"Running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd)
    
    print()
    print("=" * 70)
    
    if result.returncode == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. See output above for details.")
    
    print("=" * 70)
    
    if coverage:
        print()
        print("Coverage report generated in htmlcov/index.html")
    
    return result.returncode


def run_specific_test(test_file, test_class=None, test_method=None):
    """
    Run a specific test file, class, or method.
    
    Args:
        test_file: Name of the test file (e.g., 'test_json_parts_library.py')
        test_class: Optional test class name
        test_method: Optional test method name
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    os.chdir(project_root)
    
    # Build test path
    test_path = f"tests/{test_file}"
    
    if test_class:
        test_path += f"::{test_class}"
        if test_method:
            test_path += f"::{test_method}"
    
    cmd = ["python", "-m", "pytest", test_path, "-v", "--color=yes"]
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run JSON functionality tests")
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Verbose output")
    parser.add_argument("-c", "--coverage", action="store_true",
                       help="Generate coverage report")
    parser.add_argument("-f", "--file", type=str,
                       help="Run specific test file")
    parser.add_argument("-t", "--test", type=str,
                       help="Run specific test class or method (use with -f)")
    parser.add_argument("-q", "--quiet", action="store_true",
                       help="Minimal output")
    
    args = parser.parse_args()
    
    if args.file:
        # Run specific test
        test_class = None
        test_method = None
        
        if args.test:
            if "::" in args.test:
                test_class, test_method = args.test.split("::", 1)
            else:
                test_class = args.test
        
        exit_code = run_specific_test(args.file, test_class, test_method)
    else:
        # Run all tests
        verbose = args.verbose and not args.quiet
        exit_code = run_tests(verbose=verbose, coverage=args.coverage)
    
    sys.exit(exit_code)
