#!/usr/bin/env python3
"""
Test script for legislator discovery functionality.
"""

import os
import sys
import tempfile
import yaml
from pathlib import Path

# Add the scripts directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from legislator_discovery import LegislatorDiscovery

def create_test_data():
    """Create test YAML files for testing."""
    test_data = {
        "id": "ocd-person/12345678-1234-1234-1234-123456789012",
        "name": "Test Legislator",
        "party": [{"name": "Democratic"}],
        "roles": [
            {
                "type": "upper",
                "jurisdiction": "ak",
                "district": "District A",
                "start_date": "2023-01-01"
            }
        ]
    }
    
    # Create temporary directory structure
    temp_dir = tempfile.mkdtemp()
    test_dir = os.path.join(temp_dir, "data", "ak", "legislature")
    os.makedirs(test_dir, exist_ok=True)
    
    # Create test YAML file
    test_file = os.path.join(test_dir, "test-legislator-123.yml")
    with open(test_file, 'w') as f:
        yaml.dump(test_data, f)
    
    return temp_dir, test_file

def test_discovery():
    """Test the discovery functionality."""
    print("Testing legislator discovery...")
    
    # Create test data
    temp_dir, test_file = create_test_data()
    
    try:
        # Initialize discovery
        discovery = LegislatorDiscovery(
            openstates_path=temp_dir,
            max_legislators=10,
            force_update=True,
            locale_filter=""
        )
        
        # Discover legislators
        legislators = discovery.discover_legislators()
        
        print(f"Found {len(legislators)} legislators")
        
        if legislators:
            legislator = legislators[0]
            print(f"Sample legislator: {legislator['name']} from {legislator['state']}")
            print(f"YAML path: {legislator['yaml_path']}")
            print(f"Output path: {legislator['output_path']}")
            
            # Test saving
            discovery.save_legislators_list(legislators, "test_legislators.json")
            print("Successfully saved legislators list")
            
        return len(legislators) > 0
        
    except Exception as e:
        print(f"Error during testing: {e}")
        return False
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        if os.path.exists("test_legislators.json"):
            os.remove("test_legislators.json")

if __name__ == "__main__":
    success = test_discovery()
    if success:
        print("✅ Discovery test passed!")
    else:
        print("❌ Discovery test failed!")
        sys.exit(1) 