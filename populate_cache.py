#!/usr/bin/env python3
"""
Standalone script to populate permacache caches.
Usage: python populate_cache.py <cache_dir> <cache_name> <function_calls>
"""

import sys
import os
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from permacache import cache
from permacache.locked_shelf import sync_all_caches, close_all_caches


def fn(x, y=2, z=3, *args):
    fn.counter += 1
    return x, y, z, args

# Initialize counter
fn.counter = 0


def parallel_fn(xs, y, z):
    parallel_fn.counter += len(xs)
    return [(x + y + z) for x in xs]

# Initialize counter
parallel_fn.counter = 0


def main():
    if len(sys.argv) != 4:
        print("Usage: python populate_cache.py <cache_dir> <cache_name> <function_calls_json>")
        print("Example: python populate_cache.py /tmp/cache test_cache '[{\"args\": [1, 2, 3]}, {\"kwargs\": {\"x\": 10, \"y\": 20, \"z\": 30}}]'")
        sys.exit(1)
    
    cache_dir = sys.argv[1]
    cache_name = sys.argv[2]
    function_calls_json = sys.argv[3]
    
    # Set the cache directory
    cache.CACHE = cache_dir
    
    try:
        # Parse the function calls
        function_calls = json.loads(function_calls_json)
        
        # Create the cached function
        cached_fn = cache.permacache(cache_name)(fn)
        
        # Make the function calls
        for call in function_calls:
            if "args" in call and "kwargs" in call:
                # Mixed arguments
                args = call["args"]
                kwargs = call["kwargs"]
                cached_fn(*args, **kwargs)
            elif "args" in call:
                # Positional arguments only
                cached_fn(*call["args"])
            elif "kwargs" in call:
                # Keyword arguments only
                cached_fn(**call["kwargs"])
            elif "parallel" in call:
                # Parallel processing
                cached_fn = cache.permacache(cache_name, parallel=("xs",))(parallel_fn)
                cached_fn(**call["parallel"])
        
        # Ensure caches are flushed
        sync_all_caches()
        close_all_caches()
        
        print(f"Successfully populated cache '{cache_name}' with {len(function_calls)} calls")
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()