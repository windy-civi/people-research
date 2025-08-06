# Simple Legislator Research

A hyper-simple GitHub Action that researches state legislators using Claude Deep Research to find campaign websites, policy issues, and donor information.

## Overview

This project clones the [OpenStates People repository](https://github.com/openstates/people) and processes active legislators to enrich their data with:

- **Campaign Issues**: Policy positions and stances from official campaign websites
- **Donor Information**: Top corporate donors, industry contributions, and ideological/single-issue donors (PACs, advocacy groups)
- **Research Metadata**: Processing timestamps, cost estimates, and source attribution

## Features

- **Simple Workflow**: Direct iteration through OpenStates people data
- **Locale Filtering**: Process specific states or all states
- **Claude Deep Research Integration**: Uses web search capabilities to find current information
- **Structured Output**: JSON files matching OpenStates directory structure
- **Error Handling**: Graceful failure handling with detailed logging
- **Scheduled Updates**: Weekly automated runs with manual trigger options

## Directory Structure

The output follows the OpenStates structure:

```
data/
├── ak/
│   └── legislature/
│       ├── john-doe-123.research.json
│       └── jane-smith-456.research.json
├── tx/
│   └── legislature/
│       └── bob-johnson-789.research.json
└── ...
```

## Research Output Format

Each `.research.json` file contains:

```json
{
  "legislator_id": "ocd-person/12345678-1234-1234-1234-123456789012",
  "name": "John Doe",
  "state": "ak",
  "last_updated": "2024-01-15T10:30:00Z",
  "issues": [
    {
      "title": "Healthcare Reform",
      "description": "Supports expanding Medicaid coverage",
      "category": "Healthcare",
      "source": "https://johndoe.com/issues"
    }
  ],
  "donors": {
    "top_companies": [
      {
        "name": "Example Corp",
        "amount": "$50,000",
        "industry": "Technology",
        "cycle": "2024"
      }
    ],
    "top_industries": [
      {
        "industry": "Healthcare",
        "total_amount": "$150,000",
        "percentage": "25%"
      }
    ],
    "ideological_donors": [
      {
        "name": "Progressive PAC",
        "amount": "$25,000",
        "ideology": "Liberal",
        "issue_focus": "Environmental Protection",
        "cycle": "2024"
      }
    ],
    "individual_donors": [
      {
        "name": "Jane Smith",
        "amount": "$5,000",
        "occupation": "Attorney"
      }
    ],
    "data_source": "OpenSecrets",
    "source_url": "https://www.opensecrets.org"
  },
  "sources": [
    "https://johndoe.com/issues",
    "https://www.opensecrets.org"
  ],
  "processing_metadata": {
    "processed_date": "2024-01-15T10:30:00Z",
    "github_action_run": "123456789",
    "tokens_used": {
      "input_tokens": 1500,
      "output_tokens": 800
    }
  }
}
```

## Setup

### Prerequisites

1. **Anthropic API Key**: Required for Claude Deep Research
2. **GitHub Repository**: This project should be in a GitHub repository
3. **GitHub Secrets**: Add your Anthropic API key as a secret

### Installation

1. Clone this repository
2. Add your Anthropic API key as a GitHub secret named `ANTHROPIC_API_KEY`
3. The workflow will run automatically on schedule or can be triggered manually

### Local Development with Act

For local development and testing, use [act](https://github.com/nektos/act):

```bash
# Install act (macOS)
brew install act

# Install act (Linux)
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run the workflow locally
act workflow_dispatch

# Run with specific inputs
act workflow_dispatch -e <(echo '{"inputs": {"max_legislators": "5", "locale_filter": "ak"}}')

# Run in dry-run mode to see what would happen
act workflow_dispatch --dryrun
```

**Note**: When using `act`, you'll need to set up your `ANTHROPIC_API_KEY` as an environment variable:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

### Testing Scripts Locally

You can also test individual scripts directly:

```bash
# Install dependencies
pip install -r requirements.txt

# Clone OpenStates people repo for testing
git clone https://github.com/openstates/people.git openstates-people

# Test with a single legislator (requires API key)
export ANTHROPIC_API_KEY="your-api-key-here"
python scripts/legislator_researcher.py openstates-people/data/us/legislature/john-doe.yml output.json

# Test the simple researcher
export LOCALE="us"
export MAX_PEOPLE="5"
python scripts/simple_researcher.py openstates-people .

# Test the setup
python scripts/test_simple.py
```

### GitHub Secrets

| Secret Name | Description |
|-------------|-------------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key for Claude Deep Research |

## Usage

### Manual Trigger

1. Go to your repository's Actions tab
2. Select "Simple Legislator Research"
3. Click "Run workflow"
4. Configure options:
   - **Locale**: Specific state to process (e.g., "ak", "tx", "us") or leave empty for all
   - **Max People**: Number of people to process (default: 10)

### Scheduled Runs

The workflow runs automatically every Sunday at 2 AM UTC, processing up to 10 people that need research.

### Output Files

- **Individual Research**: `data/{state}/legislature/{name}.research.json`
- **Processing Logs**: Available in GitHub Actions logs

## Configuration

### Workflow Inputs

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `locale` | string | "us" | Specific locale to process (or empty for all) |
| `max_people` | string | "10" | Maximum people to process |

### Processing

- **Sequential Processing**: Simple one-by-one processing to respect API limits
- **Error Handling**: Individual failures don't stop the entire workflow
- **Skip Existing**: Automatically skips people who already have research data

## Error Handling

- **Individual Failures**: Failed research jobs create error responses
- **Network Issues**: Graceful degradation with detailed logging
- **API Limits**: Sequential processing to respect rate limits
- **Data Validation**: JSON validation and error logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with a small dataset
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [OpenStates People](https://github.com/openstates/people) for the legislator data
- [Anthropic](https://www.anthropic.com/) for Claude Deep Research capabilities
- GitHub Actions for the automation platform

## Support

For issues or questions:
1. Check the GitHub Actions logs for detailed error information
2. Review the individual research files in `data/` for processing results
3. Open an issue in this repository

## Security

- API keys are stored as GitHub secrets
- No sensitive data is logged
- Processing metadata is anonymized
- All research data is publicly accessible (as intended) 