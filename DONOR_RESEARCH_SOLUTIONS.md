# Donor Research Solutions

## Problem Analysis

The current `legislator_researcher.py` script has several issues with donor data:

1. **Fictional/Inaccurate Data**: The donor information appears to be generated rather than scraped from real sources
2. **Incorrect URLs**: The source URLs don't match actual OpenSecrets URLs
3. **Missing Real-time Data**: No actual web scraping or API access to get current donor information

## Solutions Provided

### 1. Split Research Approach (`legislator_researcher.py` - Modified)

**What it does:**
- Separates issues research (using Claude) from donor research (using web scraping)
- Uses a dedicated `donor_researcher.py` script for scraping OpenSecrets
- More reliable for issues research, but requires additional setup for donor data

**Pros:**
- Cleaner separation of concerns
- Issues research remains accurate
- Modular design

**Cons:**
- Requires additional script (`donor_researcher.py`)
- Donor scraping needs OpenSecrets API access for full functionality

**Usage:**
```bash
python scripts/legislator_researcher.py <yaml_file> <output_json>
```

### 2. Enhanced Web Search Approach (`enhanced_legislator_researcher.py`)

**What it does:**
- Uses Claude with web search tools to access real-time data
- Searches OpenSecrets.org and other sources directly
- Gets current donor information and correct URLs

**Pros:**
- Most accurate donor data
- Correct source URLs
- Real-time information
- Single script solution

**Cons:**
- Requires Claude Sonnet 3.5 (more expensive)
- Depends on web search availability
- May be slower due to web searches

**Usage:**
```bash
python scripts/enhanced_legislator_researcher.py <yaml_file> <output_json>
```

### 3. Dedicated Donor Scraper (`donor_researcher.py`)

**What it does:**
- Standalone script for scraping OpenSecrets donor data
- Can be used independently or integrated with the main researcher
- Handles URL discovery and data extraction

**Pros:**
- Focused on donor data only
- Can be run independently
- Good for testing donor scraping

**Cons:**
- Requires OpenSecrets API access for full functionality
- Limited to donor data only

**Usage:**
```bash
python scripts/donor_researcher.py "Katie Britt" "Alabama"
```

## Recommended Approach

### For Production Use: Enhanced Web Search

Use `enhanced_legislator_researcher.py` because:
1. **Most Accurate**: Gets real-time data from OpenSecrets
2. **Correct URLs**: Generates proper OpenSecrets URLs
3. **Comprehensive**: Handles both issues and donors in one script
4. **Current Data**: Always gets the latest donor information

### For Development/Testing: Split Approach

Use the modified `legislator_researcher.py` with `donor_researcher.py` because:
1. **Cost Effective**: Uses cheaper Claude Haiku for issues
2. **Modular**: Can test donor scraping separately
3. **Flexible**: Can swap out donor research methods

## Implementation Steps

### Option 1: Switch to Enhanced Researcher

1. Replace your current script calls:
```bash
# Instead of:
python scripts/legislator_researcher.py <yaml> <output>

# Use:
python scripts/enhanced_legislator_researcher.py <yaml> <output>
```

2. Update your GitHub Actions or automation scripts to use the enhanced version

### Option 2: Improve Current Script

1. Install the donor researcher:
```bash
# Make sure donor_researcher.py is in your scripts directory
```

2. The modified `legislator_researcher.py` will automatically use it when available

## Expected Improvements

With the enhanced approach, you should see:

1. **Accurate Donor Data**: Real company names and amounts from OpenSecrets
2. **Correct URLs**: Proper OpenSecrets URLs like `https://www.opensecrets.org/members-of-congress/katie-britt/contributors`
3. **Current Information**: 2024 cycle data instead of outdated information
4. **Comprehensive Lists**: Full donor lists matching OpenSecrets.org

## Example Output Comparison

### Current (Inaccurate):
```json
{
  "donors": {
    "top_companies": [
      {
        "name": "Blue Cross Blue Shield",
        "amount": "$25,000-$50,000",
        "industry": "Healthcare",
        "cycle": "2022"
      }
    ],
    "source_url": "https://www.opensecrets.org/candidates/summary?cycle=2022&cid=N00044656"
  }
}
```

### Enhanced (Accurate):
```json
{
  "donors": {
    "top_companies": [
      {
        "name": "Blue Cross Blue Shield",
        "amount": "$15,000",
        "industry": "Health",
        "cycle": "2024"
      },
      {
        "name": "Alabama Power Co",
        "amount": "$10,000",
        "industry": "Energy",
        "cycle": "2024"
      }
    ],
    "source_url": "https://www.opensecrets.org/members-of-congress/katie-britt/contributors"
  }
}
```

## Next Steps

1. **Test the Enhanced Script**: Try it with a few legislators to verify accuracy
2. **Update Automation**: Modify your GitHub Actions to use the enhanced version
3. **Monitor Results**: Check that the donor data matches OpenSecrets.org
4. **Consider API Access**: For even better results, get OpenSecrets API access

## Troubleshooting

### If donor data is still inaccurate:
1. Check that you're using the enhanced script
2. Verify your Anthropic API key has web search access
3. Try running the donor researcher separately to test scraping

### If URLs are still wrong:
1. The enhanced script should generate correct URLs
2. Check that the web search is finding the right OpenSecrets pages
3. Verify the legislator name matches OpenSecrets format

### If you get errors:
1. Check the logs for specific error messages
2. Verify all dependencies are installed
3. Test with a simple legislator first
