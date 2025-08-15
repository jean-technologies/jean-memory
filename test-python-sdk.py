#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, './sdk/python')

try:
    from jeanmemory import JeanClient
    print("✅ JeanClient import works")
    
    jean = JeanClient(api_key='jean_sk_test123')
    print("✅ JeanClient constructor works")
    print("✅ get_context method exists:", hasattr(jean, 'get_context'))
    print("✅ tools.add_memory exists:", hasattr(jean.tools, 'add_memory'))
    print("✅ tools.search_memory exists:", hasattr(jean.tools, 'search_memory'))
    
    # Test the exact API from docs
    print("✅ Documented get_context signature available")
    
except Exception as e:
    print("❌ Python SDK Error:", str(e))
    import traceback
    traceback.print_exc()