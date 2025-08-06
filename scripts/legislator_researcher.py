#!/usr/bin/env python3
"""
Legislator Research Script

This script processes individual legislator data from OpenStates and uses Claude
to find campaign websites, issues, and donor information.
"""

import os
import json
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from anthropic import Anthropic
import anthropic
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LegislatorResearcher:
    def __init__(self, api_key: str):
        """Initialize the researcher with Anthropic API key."""
        # Clear any proxy environment variables that might interfere
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        for var in proxy_vars:
            if var in os.environ:
                logger.info(f"Clearing proxy environment variable: {var}")
                del os.environ[var]
        
        try:
            self.anthropic = Anthropic(api_key=api_key)
            logger.info("Anthropic client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
            raise
        
    def load_legislator_data(self, yaml_path: str) -> Dict[str, Any]:
        """Load legislator data from YAML file."""
        try:
            # Check if file exists
            if not os.path.exists(yaml_path):
                logger.error(f"File does not exist: {yaml_path}")
                logger.info(f"Current working directory: {os.getcwd()}")
                logger.info(f"Directory contents: {os.listdir('.')}")
                if os.path.exists('openstates-people'):
                    logger.info(f"openstates-people contents: {os.listdir('openstates-people')}")
                raise FileNotFoundError(f"File not found: {yaml_path}")
            
            with open(yaml_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except Exception as e:
            logger.error(f"Error loading YAML file {yaml_path}: {e}")
            raise
    
    def create_research_prompt(self, legislator_data: Dict[str, Any]) -> str:
        """Create a comprehensive research prompt for Claude."""
        name = legislator_data.get('name', 'Unknown')
        party = legislator_data.get('party', [{}])[0].get('name', 'Unknown') if legislator_data.get('party') else 'Unknown'
        
        # Extract role information
        roles = legislator_data.get('roles', [])
        current_role = None
        for role in roles:
            if role.get('type') in ['upper', 'lower', 'legislature'] and not role.get('end_date'):
                current_role = role
                break
        
        state = current_role.get('jurisdiction', 'Unknown') if current_role else 'Unknown'
        district = current_role.get('district', '') if current_role else ''
        chamber = current_role.get('type', 'legislature') if current_role else 'legislature'
        
        prompt = f"""Research {name}, a {party} {chamber} legislator from {state} district {district}.

Based on your knowledge, provide information about their campaign issues and donor information.

For donors, include both corporate AND ideological/single-issue donors (PACs, advocacy groups, etc.).

Output ONLY valid JSON in this exact structure:
{{
  "legislator_id": "{legislator_data.get('id', '')}",
  "name": "{name}",
  "state": "{state}",
  "last_updated": "{self._get_current_time()}",
  "issues": [
    {{
      "title": "Issue Title",
      "description": "Their specific stance or position",
      "category": "Policy category (healthcare, education, etc.)",
      "source": "URL or source of information"
    }}
  ],
  "donors": {{
    "top_companies": [
      {{
        "name": "Company/Organization Name",
        "amount": "Dollar amount or range if available",
        "industry": "Industry classification",
        "cycle": "Election cycle (e.g., 2024, 2022)"
      }}
    ],
    "top_industries": [
      {{
        "industry": "Industry Name",
        "total_amount": "Total contributions if available",
        "percentage": "Percentage of total if available"
      }}
    ],
    "ideological_donors": [
      {{
        "name": "PAC/Advocacy group name",
        "amount": "Dollar amount or range if available",
        "ideology": "Conservative/Liberal/Single-issue description",
        "issue_focus": "Specific issue they advocate for",
        "cycle": "Election cycle"
      }}
    ],
    "individual_donors": [
      {{
        "name": "Individual donor name",
        "amount": "Amount if available",
        "occupation": "Occupation if available"
      }}
    ],
    "data_source": "Source of donor information (OpenSecrets, FEC, state records, etc.)",
    "source_url": "URL to donor database or records"
  }},
  "sources": [
    "List of primary sources used for this research"
  ]
}}

Be efficient - provide information based on your knowledge about their campaign issues and donor information.

IMPORTANT: Output ONLY valid JSON. Do not include any explanatory text, markdown formatting, or code blocks. The response should be a single JSON object that can be parsed directly."""
        
        return prompt
    
    def _get_current_time(self) -> str:
        """Get current time in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def research_legislator(self, legislator_data: Dict[str, Any]) -> Dict[str, Any]:
        """Research a single legislator using Claude with tools."""
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                prompt = self.create_research_prompt(legislator_data)
                
                # Add retry instruction if this is a retry
                if attempt > 0:
                    prompt += f"\n\nRETRY ATTEMPT {attempt + 1}: Please ensure you output ONLY valid JSON without any markdown formatting, code blocks, or explanatory text."
                
                # Use the latest Claude Sonnet 4 model
                message = self.anthropic.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=3000,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                
                # Extract text from the response
                text_blocks = [block for block in message.content if hasattr(block, 'type') and block.type == "text"]
                if text_blocks:
                    final_response = text_blocks[0].text
                else:
                    final_response = "No text response received"
                
                # Extract JSON from final response
                json_match = self._extract_json_from_response(final_response)
                
                if json_match:
                    try:
                        json_data = json.loads(json_match)
                        
                        # Add processing metadata
                        json_data["processing_metadata"] = {
                            "processed_date": self._get_current_time(),
                            "github_action_run": os.environ.get("GITHUB_RUN_ID", "unknown"),
                            "tokens_used": {
                                "input_tokens": message.usage.input_tokens if message.usage else "unknown",
                                "output_tokens": message.usage.output_tokens if message.usage else "unknown"
                            },
                            "model": "claude-sonnet-4-20250514"
                        }
                        
                        return json_data
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse extracted JSON: {e}")
                        logger.error(f"Extracted JSON: {json_match}")
                        raise ValueError(f"Invalid JSON structure: {e}")
                else:
                    # Log the full response for debugging
                    logger.error(f"Full Claude response: {final_response}")
                    
                    # If this is the last attempt, raise the error
                    if attempt == max_retries:
                        raise ValueError("No valid JSON found in Claude response after all retries")
                    else:
                        logger.info(f"Retrying research for {legislator_data.get('name', 'Unknown')} (attempt {attempt + 2}/{max_retries + 1})")
                        continue
                        
            except Exception as e:
                logger.error(f"Research error for {legislator_data.get('name', 'Unknown')}: {e}")
                return self._create_error_response(legislator_data, str(e))
    

    
    def _extract_json_from_response(self, response_text: str) -> Optional[str]:
        """Extract JSON from Claude's response."""
        import re
        
        # Log the response for debugging
        logger.debug(f"Raw response: {response_text[:500]}...")
        
        # Try multiple patterns to find JSON
        patterns = [
            r'\{[\s\S]*\}',  # Basic JSON object
            r'```json\s*(\{[\s\S]*?\})\s*```',  # JSON in code blocks
            r'```\s*(\{[\s\S]*?\})\s*```',  # JSON in generic code blocks
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                try:
                    # Clean up the match
                    json_str = match.strip()
                    # Validate JSON
                    json.loads(json_str)
                    logger.debug(f"Found valid JSON with pattern: {pattern}")
                    return json_str
                except json.JSONDecodeError as e:
                    logger.debug(f"Invalid JSON with pattern {pattern}: {e}")
                    continue
        
        # If no JSON found, try to extract a basic structure
        logger.warning("No valid JSON found in response, attempting to create basic structure")
        return None
    
    def _create_error_response(self, legislator_data: Dict[str, Any], error_message: str) -> Dict[str, Any]:
        """Create an error response when research fails."""
        return {
            "legislator_id": legislator_data.get("id", ""),
            "name": legislator_data.get("name", "Unknown"),
            "state": legislator_data.get("roles", [{}])[0].get("jurisdiction", "Unknown") if legislator_data.get("roles") else "Unknown",
            "error": error_message,
            "last_updated": self._get_current_time(),
            "issues": [],
            "donors": {
                "top_companies": [],
                "top_industries": [],
                "ideological_donors": [],
                "individual_donors": [],
                "data_source": "Error occurred",
                "source_url": ""
            },
            "sources": [],
            "processing_metadata": {
                "processed_date": self._get_current_time(),
                "github_action_run": os.environ.get("GITHUB_RUN_ID", "unknown"),
                "error": True,
                "model": "claude-sonnet-4-20250514"
            }
        }
    
    def save_research_result(self, result: Dict[str, Any], output_path: str):
        """Save research result to JSON file."""
        try:
            # Ensure directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as file:
                json.dump(result, file, indent=2, ensure_ascii=False)
            
            logger.info(f"Research result saved to {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving result to {output_path}: {e}")
            raise

def main():
    """Main function to process a single legislator."""
    if len(sys.argv) != 3:
        print("Usage: python legislator_researcher.py <yaml_file_path> <output_json_path>")
        sys.exit(1)
    
    yaml_path = sys.argv[1]
    output_path = sys.argv[2]
    
    # Log environment for debugging
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Anthropic version: {anthropic.__version__}")
    logger.info(f"Working directory: {os.getcwd()}")
    
    # Get API key from environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.error("ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)
    
    try:
        # Initialize researcher
        logger.info("Initializing LegislatorResearcher...")
        researcher = LegislatorResearcher(api_key)
        
        # Load legislator data
        logger.info(f"Loading legislator data from {yaml_path}")
        legislator_data = researcher.load_legislator_data(yaml_path)
        
        # Research legislator
        logger.info(f"Researching {legislator_data.get('name', 'Unknown')}")
        result = researcher.research_legislator(legislator_data)
        
        # Save result
        researcher.save_research_result(result, output_path)
        
        # Log summary
        issues_count = len(result.get("issues", []))
        donors_count = len(result.get("donors", {}).get("top_companies", [])) + len(result.get("donors", {}).get("ideological_donors", []))
        
        logger.info(f"Research completed:")
        logger.info(f"- Issues found: {issues_count}")
        logger.info(f"- Donors found: {donors_count}")
        if result.get("error"):
            logger.warning(f"Error occurred: {result['error']}")
        
    except Exception as e:
        logger.error(f"Failed to process legislator: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()