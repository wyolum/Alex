#!/usr/bin/env python3
"""
Test script to verify urllib3 2.6.0 is installed and working correctly.
This version includes the fix for CVE-2025-66418 (unbounded decompression chain vulnerability).
"""

import urllib3
import requests

def test_urllib3_version():
    """Verify urllib3 version is 2.6.0 or higher"""
    print(f"urllib3 version: {urllib3.__version__}")
    
    # Parse version
    major, minor, patch = map(int, urllib3.__version__.split('.'))
    
    if major > 2 or (major == 2 and minor >= 6):
        print("✓ urllib3 version is secure (2.6.0+)")
        print("✓ CVE-2025-66418 vulnerability has been patched")
        return True
    else:
        print("✗ urllib3 version is vulnerable!")
        print("✗ Please upgrade to urllib3 2.6.0 or higher")
        return False

def test_requests_compatibility():
    """Verify requests library works with urllib3 2.6.0"""
    print(f"\nrequests version: {requests.__version__}")
    
    try:
        # Make a simple request to verify compatibility
        response = requests.get('https://httpbin.org/get', timeout=5)
        print(f"✓ requests library is compatible with urllib3 {urllib3.__version__}")
        print(f"✓ Test request successful (status code: {response.status_code})")
        return True
    except Exception as e:
        print(f"✗ Error making request: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing urllib3 Security Fix (CVE-2025-66418)")
    print("=" * 60)
    
    version_ok = test_urllib3_version()
    compat_ok = test_requests_compatibility()
    
    print("\n" + "=" * 60)
    if version_ok and compat_ok:
        print("✓ All tests passed! Environment is secure and functional.")
    else:
        print("✗ Some tests failed. Please review the output above.")
    print("=" * 60)
