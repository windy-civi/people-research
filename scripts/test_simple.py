#!/usr/bin/env python3
"""
Simple Test Script

This script tests the simplified researcher workflow.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

def test_simple_researcher():
    """Test the simple researcher workflow."""
    print("Testing Simple Researcher...")
    
    # Check if openstates-people directory exists
    if not os.path.exists("openstates-people"):
        print("❌ openstates-people directory not found")
        print("Please run: git clone https://github.com/openstates/people.git openstates-people")
        return False
    
    # Check if simple_researcher.py exists
    if not os.path.exists("scripts/simple_researcher.py"):
        print("❌ scripts/simple_researcher.py not found")
        return False
    
    # Check if legislator_researcher.py exists
    if not os.path.exists("scripts/legislator_researcher.py"):
        print("❌ scripts/legislator_researcher.py not found")
        return False
    
    # Check if requirements.txt exists
    if not os.path.exists("requirements.txt"):
        print("❌ requirements.txt not found")
        return False
    
    # Check if workflow file exists
    if not os.path.exists(".github/workflows/research-people.yml"):
        print("❌ .github/workflows/research-people.yml not found")
        return False
    
    # Check if data directory structure can be created
    try:
        os.makedirs("data/test/legislature", exist_ok=True)
        print("✅ Data directory structure can be created")
    except Exception as e:
        print(f"❌ Cannot create data directory: {e}")
        return False
    
    # Check if we can find YAML files in openstates-people
    yaml_files = []
    for root, dirs, files in os.walk("openstates-people/data"):
        for file in files:
            if file.endswith('.yml'):
                yaml_files.append(os.path.join(root, file))
    
    if not yaml_files:
        print("❌ No YAML files found in openstates-people/data")
        return False
    
    print(f"✅ Found {len(yaml_files)} YAML files in openstates-people")
    
    # Test environment variables
    locale = os.getenv('LOCALE', 'us')
    max_people = os.getenv('MAX_PEOPLE', '10')
    api_key = os.getenv('ANTHROPIC_API_KEY', '')
    
    print(f"✅ Environment variables:")
    print(f"   LOCALE: {locale}")
    print(f"   MAX_PEOPLE: {max_people}")
    print(f"   ANTHROPIC_API_KEY: {'Set' if api_key else 'Not set'}")
    
    print("\n✅ All basic tests passed!")
    print("\nTo run the actual research:")
    print("1. Set your ANTHROPIC_API_KEY environment variable")
    print("2. Run: python scripts/simple_researcher.py openstates-people .")
    
    return True

if __name__ == "__main__":
    success = test_simple_researcher()
    sys.exit(0 if success else 1) 