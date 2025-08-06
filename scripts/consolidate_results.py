#!/usr/bin/env python3
"""
Consolidate Results Script

This script consolidates research results and generates summary statistics.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ResultsConsolidator:
    def __init__(self):
        """Initialize the consolidator."""
        pass
    
    def consolidate_results(self) -> Dict[str, Any]:
        """Consolidate all research results and generate summary."""
        results = []
        state_stats = {}
        total_cost = 0.0
        
        # Scan for research files
        research_files = self._find_research_files("data")
        logger.info(f"Found {len(research_files)} research files")
        
        for research_file in research_files:
            try:
                data = self._load_research_file(research_file)
                if data:
                    state = data.get('state', 'Unknown')
                    
                    # Initialize state stats if needed
                    if state not in state_stats:
                        state_stats[state] = {
                            'processed': 0,
                            'issues': 0,
                            'donors': 0,
                            'errors': 0
                        }
                    
                    # Update state stats
                    state_stats[state]['processed'] += 1
                    state_stats[state]['issues'] += len(data.get('issues', []))
                    
                    donors_count = (
                        len(data.get('donors', {}).get('top_companies', [])) +
                        len(data.get('donors', {}).get('ideological_donors', []))
                    )
                    state_stats[state]['donors'] += donors_count
                    
                    if data.get('error'):
                        state_stats[state]['errors'] += 1
                    
                    # Estimate cost
                    cost = self._estimate_cost(data)
                    total_cost += cost
                    
                    # Add to results
                    results.append({
                        'name': data.get('name', 'Unknown'),
                        'state': state,
                        'issues_count': len(data.get('issues', [])),
                        'donors_count': donors_count,
                        'has_error': bool(data.get('error')),
                        'last_updated': data.get('last_updated', ''),
                        'cost': cost
                    })
                    
            except Exception as e:
                logger.warning(f"Error processing {research_file}: {e}")
                continue
        
        # Generate summary
        summary = self._generate_summary(results, state_stats, total_cost)
        
        return summary
    
    def _find_research_files(self, directory: str) -> List[str]:
        """Find all research JSON files in the directory structure."""
        research_files = []
        
        if not os.path.exists(directory):
            return research_files
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.research.json'):
                    research_files.append(os.path.join(root, file))
        
        return research_files
    
    def _load_research_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load a research JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading {file_path}: {e}")
            return None
    
    def _estimate_cost(self, data: Dict[str, Any]) -> float:
        """Estimate the cost of processing this research."""
        try:
            metadata = data.get('processing_metadata', {})
            tokens_used = metadata.get('tokens_used', {})
            
            if isinstance(tokens_used, dict):
                input_tokens = tokens_used.get('input_tokens', 0)
                output_tokens = tokens_used.get('output_tokens', 0)
                
                # Rough cost estimation (adjust based on actual pricing)
                input_cost = (input_tokens / 1000000) * 3  # $3 per 1M input tokens
                output_cost = (output_tokens / 1000000) * 15  # $15 per 1M output tokens
                
                return input_cost + output_cost
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _generate_summary(self, results: List[Dict[str, Any]], state_stats: Dict[str, Any], total_cost: float) -> Dict[str, Any]:
        """Generate summary statistics."""
        successful = len([r for r in results if not r['has_error']])
        errors = len([r for r in results if r['has_error']])
        total_issues = sum(r['issues_count'] for r in results)
        total_donors = sum(r['donors_count'] for r in results)
        
        summary = {
            'run_date': datetime.now().isoformat(),
            'total_processed': len(results),
            'successful': successful,
            'errors': errors,
            'total_issues': total_issues,
            'total_donors': total_donors,
            'estimated_cost_usd': round(total_cost, 2),
            'by_state': state_stats,
            'legislators': sorted(results, key=lambda x: (x['state'], x['name']))
        }
        
        return summary
    
    def save_summary(self, summary: Dict[str, Any], output_file: str = "research_summary.json"):
        """Save summary to file."""
        try:
            with open(output_file, 'w', encoding='utf-8') as file:
                json.dump(summary, file, indent=2, ensure_ascii=False)
            
            logger.info(f"Summary saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving summary: {e}")
            raise
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print summary to console."""
        print("\n" + "="*50)
        print("LEGISLATOR RESEARCH SUMMARY")
        print("="*50)
        print(f"Processed: {summary['total_processed']} legislators")
        print(f"Successful: {summary['successful']}")
        print(f"Errors: {summary['errors']}")
        print(f"Total Issues Found: {summary['total_issues']}")
        print(f"Total Donors Found: {summary['total_donors']}")
        print(f"Estimated Cost: ${summary['estimated_cost_usd']}")
        print("\nBy State:")
        
        for state, stats in sorted(summary['by_state'].items()):
            print(f"  {state.upper()}: {stats['processed']} processed, "
                  f"{stats['issues']} issues, {stats['donors']} donors")
        
        print("="*50)

def main():
    """Main function to consolidate results."""
    try:
        # Initialize consolidator
        consolidator = ResultsConsolidator()
        
        # Consolidate results
        logger.info("Starting results consolidation...")
        summary = consolidator.consolidate_results()
        
        # Save summary
        consolidator.save_summary(summary)
        
        # Print summary
        consolidator.print_summary(summary)
        
        logger.info("Consolidation completed successfully")
        
    except Exception as e:
        logger.error(f"Consolidation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 