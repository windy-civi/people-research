#!/usr/bin/env python3
"""
Donor Research Script

This script scrapes donor information from OpenSecrets and other sources
for individual legislators.
"""

import os
import json
import requests
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import re
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DonorResearcher:
    def __init__(self):
        """Initialize the donor researcher."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def get_opensecrets_url(self, name: str, state: str) -> str:
        """Generate OpenSecrets URL for a legislator."""
        # Clean the name for URL
        clean_name = name.lower().replace(' ', '-')
        return f"https://www.opensecrets.org/members-of-congress/{clean_name}/contributors"
    
    def scrape_opensecrets_page(self, url: str) -> Dict[str, Any]:
        """Scrape donor information from OpenSecrets page."""
        try:
            logger.info(f"Scraping: {url}")
            
            # Add delay to be respectful
            time.sleep(2)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract donor information
            donors = {
                "top_companies": [],
                "top_industries": [],
                "ideological_donors": [],
                "individual_donors": [],
                "data_source": "OpenSecrets",
                "source_url": url,
                "scraped_date": self._get_current_time()
            }
            
            # Look for donor tables
            tables = soup.find_all('table')
            for table in tables:
                # Look for company donors
                rows = table.find_all('tr')
                for row in rows[1:]:  # Skip header
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        company_name = cells[0].get_text(strip=True)
                        amount = cells[1].get_text(strip=True)
                        industry = cells[2].get_text(strip=True) if len(cells) > 2 else "Unknown"
                        
                        if company_name and amount:
                            donors["top_companies"].append({
                                "name": company_name,
                                "amount": amount,
                                "industry": industry,
                                "cycle": "2024"  # Default to current cycle
                            })
            
            # Look for industry breakdown
            industry_sections = soup.find_all('div', class_=re.compile(r'industry|sector', re.I))
            for section in industry_sections:
                # Extract industry information
                pass
            
            logger.info(f"Found {len(donors['top_companies'])} company donors")
            return donors
            
        except requests.RequestException as e:
            logger.error(f"Request error scraping {url}: {e}")
            return self._create_error_donors(url, str(e))
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return self._create_error_donors(url, str(e))
    
    def search_legislator_opensecrets(self, name: str, state: str) -> Optional[str]:
        """Search for a legislator on OpenSecrets to find their profile URL."""
        try:
            # Try different URL patterns
            patterns = [
                f"https://www.opensecrets.org/members-of-congress/{name.lower().replace(' ', '-')}/contributors",
                f"https://www.opensecrets.org/members-of-congress/{name.lower().replace(' ', '')}/contributors",
                f"https://www.opensecrets.org/members-of-congress/{name.lower().replace(' ', '_')}/contributors"
            ]
            
            for pattern in patterns:
                try:
                    response = self.session.head(pattern, timeout=10)
                    if response.status_code == 200:
                        logger.info(f"Found OpenSecrets URL: {pattern}")
                        return pattern
                except:
                    continue
            
            # If no direct match, try searching
            search_url = f"https://www.opensecrets.org/search?q={quote(name)}"
            response = self.session.get(search_url, timeout=30)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for links to member profiles
            links = soup.find_all('a', href=re.compile(r'/members-of-congress/.*/contributors'))
            if links:
                href = links[0]['href']
                full_url = urljoin('https://www.opensecrets.org', href)
                logger.info(f"Found OpenSecrets URL via search: {full_url}")
                return full_url
            
            return None
            
        except Exception as e:
            logger.error(f"Error searching for legislator {name}: {e}")
            return None
    
    def research_donors(self, name: str, state: str) -> Dict[str, Any]:
        """Research donor information for a legislator."""
        logger.info(f"Researching donors for {name} from {state}")
        
        # First try to find the correct OpenSecrets URL
        opensecrets_url = self.search_legislator_opensecrets(name, state)
        
        if opensecrets_url:
            return self.scrape_opensecrets_page(opensecrets_url)
        else:
            # Fallback to generated URL
            fallback_url = self.get_opensecrets_url(name, state)
            logger.warning(f"Could not find OpenSecrets URL, using fallback: {fallback_url}")
            return self.scrape_opensecrets_page(fallback_url)
    
    def _create_error_donors(self, url: str, error_message: str) -> Dict[str, Any]:
        """Create error response for donor research."""
        return {
            "top_companies": [],
            "top_industries": [],
            "ideological_donors": [],
            "individual_donors": [],
            "data_source": "Error occurred",
            "source_url": url,
            "error": error_message,
            "scraped_date": self._get_current_time()
        }
    
    def _get_current_time(self) -> str:
        """Get current time in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()

def main():
    """Main function to test donor research."""
    if len(sys.argv) != 3:
        print("Usage: python donor_researcher.py <legislator_name> <state>")
        print("Example: python donor_researcher.py 'Katie Britt' 'Alabama'")
        sys.exit(1)
    
    name = sys.argv[1]
    state = sys.argv[2]
    
    try:
        researcher = DonorResearcher()
        result = researcher.research_donors(name, state)
        
        # Save result
        output_file = f"donor_research_{name.replace(' ', '_').lower()}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Donor research saved to {output_file}")
        logger.info(f"Found {len(result.get('top_companies', []))} company donors")
        
    except Exception as e:
        logger.error(f"Failed to research donors: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
