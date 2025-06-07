# CRM Lead Generation AI Agent

A comprehensive AI-powered lead generation system that combines web scraping, local LLM processing, and cloud API fallback to generate high-quality CRM leads from multiple data sources.

## Quick Links
- [Quick Start Guide](QUICK_START.md)
- [Development Progress](DEVELOPMENT_PROGRESS.md) 
- [Cloud API Setup](CLOUD_API_SETUP.md)
- [Enhanced CRM Summary](ENHANCED_CRM_SUMMARY.md)
- [Requirements](../Requirements.md)

## Project Structure

```
CRM_lead_geneartor/
├── config/                 # Configuration files
├── data/                   # Data storage and outputs
├── docs/                   # Documentation
├── scripts/                # Setup and utility scripts
├── src/                    # Source code
│   ├── agents/            # AI agent implementations
│   ├── config/            # Configuration modules
│   ├── processors/        # Data processing modules
│   ├── scrapers/          # Web scraping modules
│   ├── tools/             # Agent tools
│   └── utils/             # Helper utilities
├── tests/                 # Test files
└── main.py                # Main application entry point
```

## Features

- **Multi-Source Data Collection**: Scrapes from business directories, ISP listings, and government databases
- **AI-Powered Classification**: Uses local LLMs with cloud API fallback for industry classification
- **Smart Validation**: Multi-source verification and confidence scoring
- **Flexible Output**: Comprehensive CSV exports with CRM-ready data fields
- **Geographic Processing**: Intelligent state-based data collection and subdivision

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure your settings in `config/` directory
4. Run the application: `python main.py`

For detailed setup instructions, see [Quick Start Guide](QUICK_START.md).

## Development

See [Development Tasks](../devtasks.md) for current development status and task tracking.

## License

See project documentation for licensing information. 