#!/usr/bin/env python3
"""
Simple Researcher Script

This script directly iterates through OpenStates people data, checks if we already have
research for each person, and if not, performs the research and saves directly to the repo.
"""

import os
import json
import yaml
import sys
import glob
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleResearcher:
    def __init__(self, openstates_path: str, research_repo_path: str):
        """Initialize the simple researcher."""
        self.locale = os.getenv('LOCALE', '').strip()
        self.max_people = int(os.getenv('MAX_PEOPLE', '10'))
        self.openstates_path = openstates_path
        self.research_repo_path = research_repo_path
        
    def run(self):
        """Main execution method."""
        logger.info(f"Starting simple research for locale: {self.locale or 'all'}")
        logger.info(f"Max people to process: {self.max_people}")
        
        # Find people to research
        people_to_research = self._find_people_to_research()
        
        if not people_to_research:
            logger.info("No people found to research")
            return
        
        logger.info(f"Found {len(people_to_research)} people to research")
        
        # Process each person
        processed = 0
        for person in people_to_research:
            if processed >= self.max_people:
                break
                
            try:
                self._research_person(person)
                processed += 1
                logger.info(f"✅ Processed {processed}/{len(people_to_research)}: {person['name']}")
            except Exception as e:
                logger.error(f"❌ Failed to process {person['name']}: {e}")
                continue
        
        logger.info(f"Research completed: {processed} people processed")
    
    def _find_people_to_research(self) -> List[Dict[str, Any]]:
        """Find people that need research."""
        people = []
        
        # Build glob pattern based on locale
        if self.locale:
            glob_pattern = os.path.join(self.openstates_path, "data", self.locale, "legislature", "*.yml")
        else:
            glob_pattern = os.path.join(self.openstates_path, "data", "*", "legislature", "*.yml")
        
        logger.info(f"Searching with pattern: {glob_pattern}")
        
        # Find all YAML files
        yaml_files = glob.glob(glob_pattern)
        logger.info(f"Found {len(yaml_files)} YAML files")
        
        for yaml_file in yaml_files:
            try:
                person_info = self._process_person_file(yaml_file)
                if person_info:
                    people.append(person_info)
            except Exception as e:
                logger.warning(f"Error processing {yaml_file}: {e}")
                continue
        
        # Shuffle and return
        random.shuffle(people)
        return people
    
    def _process_person_file(self, yaml_file: str) -> Optional[Dict[str, Any]]:
        """Process a single person YAML file."""
        try:
            with open(yaml_file, 'r', encoding='utf-8') as file:
                person_data = yaml.safe_load(file)
            
            # Check if person has active legislative role
            if not self._has_active_legislative_role(person_data):
                return None
            
            # Parse state and determine paths
            path_parts = yaml_file.split(os.sep)
            data_index = path_parts.index("data")
            state = path_parts[data_index + 1]
            filename = Path(yaml_file).stem
            
            # Check if we already have research data
            research_path = os.path.join(self.research_repo_path, "data", state, "legislature", f"{filename}.research.json")
            if os.path.exists(research_path):
                logger.debug(f"Already have research for {filename}")
                return None
            
            return self._create_person_info(person_data, state, filename, yaml_file)
            
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
    
    def _create_person_info(self, person_data: Dict[str, Any], state: str, filename: str, yaml_path: str) -> Dict[str, Any]:
        """Create person info dictionary."""
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
            "yaml_path": yaml_path,
            "output_path": os.path.join(self.research_repo_path, "data", state, "legislature", f"{filename}.research.json")
        }
    
    def _research_person(self, person: Dict[str, Any]):
        """Research a single person."""
        # Ensure output directory exists
        os.makedirs(os.path.dirname(person['output_path']), exist_ok=True)
        
        # Get API key from environment
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        # Import the researcher here to avoid circular imports
        from legislator_researcher import LegislatorResearcher
        
        # Create researcher instance
        researcher = LegislatorResearcher(api_key)
        
        # Load legislator data
        legislator_data = researcher.load_legislator_data(person['yaml_path'])
        
        # Perform research
        research_data = researcher.research_legislator(legislator_data)
        
        # Save directly to the repo
        with open(person['output_path'], 'w', encoding='utf-8') as f:
            json.dump(research_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved research for {person['name']} to {person['output_path']}")

def main():
    """Main function."""
    if len(sys.argv) != 3:
        print("Usage: python simple_researcher.py <openstates-people-repo-path> <research-git-repo-path>")
        print("Example: python simple_researcher.py ./openstates-people .")
        sys.exit(1)
    
    openstates_path = sys.argv[1]
    research_repo_path = sys.argv[2]
    
    # Validate paths
    if not os.path.exists(openstates_path):
        logger.error(f"OpenStates people repo path does not exist: {openstates_path}")
        sys.exit(1)
    
    if not os.path.exists(research_repo_path):
        logger.error(f"Research repo path does not exist: {research_repo_path}")
        sys.exit(1)
    
    try:
        researcher = SimpleResearcher(openstates_path, research_repo_path)
        researcher.run()
    except Exception as e:
        logger.error(f"Research failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 