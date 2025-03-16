"""
Pytest configuration file with compatibility patches.
"""

import sys
import pytest
from pathlib import Path

# Add patches directory to Python path
patches_dir = Path(__file__).parent.parent / 'patches'
sys.path.append(str(patches_dir))

@pytest.fixture(autouse=True)
def apply_compatibility_patches():
    """Apply compatibility patches for Python 3.13+."""
    try:
        import cgi
    except ImportError:
        import twisted.web.http
        import twisted_http
        
        # Monkey patch Twisted's HTTP module with modern alternatives
        twisted.web.http.parse_header = twisted_http.parse_header
        twisted.web.http.parse_multipart = twisted_http.parse_multipart
        twisted.web.http.parse_qs = twisted_http.parse_qs
        twisted.web.http.escape = twisted_http.escape
        
        # Create a compatibility module for direct cgi imports
        sys.modules['cgi'] = twisted_http 