#!/usr/bin/env python3
"""
Legislator Discovery Script

This script discovers legislators from the OpenStates people repository and identifies
which ones need research processing.
"""

import os
import json
import yaml
import sys
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LegislatorDiscovery:
    def __init__(self, openstates_path: str, max_legislators: int = 100, force_update: bool = False, locale_filter: str = ""):
        """Initialize the discovery process."""
        self.openstates_path = openstates_path
        self.max_legislators = max_legislators
        self.force_update = force_update
        self.locale_filter = locale_filter.strip()
        
    def discover_legislators(self) -> List[Dict[str, Any]]:
        """Discover legislators that need research processing."""
        legislators = []
        
        # Build glob pattern based on locale filter
        if self.locale_filter:
            glob_pattern = os.path.join(self.openstates_path, "data", self.locale_filter, "legislature", "*.yml")
        else:
            glob_pattern = os.path.join(self.openstates_path, "data", "*", "legislature", "*.yml")
        
        logger.info(f"Searching for legislators with pattern: {glob_pattern}")
        
        # Find all YAML files
        yaml_files = glob.glob(glob_pattern)
        logger.info(f"Found {len(yaml_files)} YAML files")
        
        for yaml_file in yaml_files:
            try:
                legislator_info = self._process_legislator_file(yaml_file)
                if legislator_info:
                    legislators.append(legislator_info)
                    
            except Exception as e:
                logger.warning(f"Error processing {yaml_file}: {e}")
                continue
        
        # Shuffle and limit to max
        import random
        random.shuffle(legislators)
        selected = legislators[:self.max_legislators]
        
        logger.info(f"Found {len(legislators)} legislators needing updates")
        logger.info(f"Selected {len(selected)} for processing")
        
        return selected
    
    def _process_legislator_file(self, yaml_file: str) -> Optional[Dict[str, Any]]:
        """Process a single legislator YAML file."""
        try:
            with open(yaml_file, 'r', encoding='utf-8') as file:
                person_data = yaml.safe_load(file)
            
            # Check if person has active legislative role
            has_current_role = self._has_active_legislative_role(person_data)
            if not has_current_role:
                return None
            
            # Parse state and determine paths
            path_parts = yaml_file.split(os.sep)
            data_index = path_parts.index("data")
            state = path_parts[data_index + 1]
            filename = Path(yaml_file).stem
            
            # Check if we already have research data
            research_path = f"data/{state}/legislature/{filename}.research.json"
            needs_update = self._needs_update(research_path)
            
            if needs_update or self.force_update:
                return self._create_legislator_info(person_data, state, filename)
            
            return None
            
        except Exception as e:
            logger.error(f"Error processing {yaml_file}: {e}")
            return None
    
    def _has_active_legislative_role(self, person_data: Dict[str, Any]) -> bool:
        """Check if person has an active legislative role."""
        roles = person_data.get('roles', [])
        
        for role in roles:
            if role.get('type') in ['upper', 'lower', 'legislature']:
                # Check if role is current (no end_date or end_date is in the future)
                end_date = role.get('end_date')
                if not end_date:
                    return True
                
                try:
                    end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    if end_datetime > datetime.now(end_datetime.tzinfo):
                        return True
                except (ValueError, TypeError):
                    # If we can't parse the date, assume it's current
                    return True
        
        return False
    
    def _needs_update(self, research_path: str) -> bool:
        """Check if research data needs to be updated."""
        if not os.path.exists(research_path):
            return True
        
        if self.force_update:
            return True
        
        # Check if existing data is older than 1 year
        try:
            stats = os.stat(research_path)
            one_year_ago = datetime.now() - timedelta(days=365)
            file_time = datetime.fromtimestamp(stats.st_mtime)
            return file_time < one_year_ago
        except Exception:
            return True
    
    def _create_legislator_info(self, person_data: Dict[str, Any], state: str, filename: str) -> Dict[str, Any]:
        """Create legislator info dictionary."""
        # Extract party information
        party = "Unknown"
        if person_data.get('party'):
            party = person_data['party'][0].get('name', 'Unknown')
        
        # Extract role information
        roles = person_data.get('roles', [])
        current_role = None
        for role in roles:
            if role.get('type') in ['upper', 'lower', 'legislature'] and not role.get('end_date'):
                current_role = role
                break
        
        district = current_role.get('district', '') if current_role else ''
        chamber = current_role.get('type', 'legislature') if current_role else 'legislature'
        
        return {
            "id": person_data.get('id', ''),
            "name": person_data.get('name', 'Unknown'),
            "state": state,
            "filename": filename,
            "party": party,
            "district": district,
            "chamber": chamber,
            "yaml_path": f"openstates-people/data/{state}/legislature/{filename}.yml",
            "output_path": f"data/{state}/legislature/{filename}.research.json"
        }
    
    def save_legislators_list(self, legislators: List[Dict[str, Any]], output_file: str = "legislators_to_process.json"):
        """Save the list of legislators to process."""
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(legislators, file, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved {len(legislators)} legislators to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving legislators list: {e}")
            raise

def main():
    """Main function to discover legislators."""
    if len(sys.argv) < 2:
        print("Usage: python legislator_discovery.py <openstates_path> [max_legislators] [force_update] [locale_filter]")
        sys.exit(1)
    
    openstates_path = sys.argv[1]
    max_legislators = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    force_update = sys.argv[3].lower() == 'true' if len(sys.argv) > 3 else False
    locale_filter = sys.argv[4] if len(sys.argv) > 4 else ""
    
    try:
        # Initialize discovery
        discovery = LegislatorDiscovery(
            openstates_path=openstates_path,
            max_legislators=max_legislators,
            force_update=force_update,
            locale_filter=locale_filter
        )
        
        # Discover legislators
        logger.info("Starting legislator discovery...")
        legislators = discovery.discover_legislators()
        
        # Save results
        discovery.save_legislators_list(legislators)
        
        # Output for GitHub Actions
        print(f"::set-output name=legislators::{json.dumps(legislators)}")
        
        logger.info(f"Discovery completed: {len(legislators)} legislators selected for processing")
        
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 