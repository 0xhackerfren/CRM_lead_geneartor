# CRM Lead Generation AI Agent

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A comprehensive AI-powered lead generation system that combines web scraping, local LLM processing, and cloud API fallback to generate high-quality CRM leads from multiple data sources.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

For detailed setup instructions, see [Quick Start Guide](docs/QUICK_START.md).

## 📁 Project Structure

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
├── main.py                # Main application entry point
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## ✨ Features

- **🔍 Multi-Source Data Collection**: Scrapes from business directories, ISP listings, and government databases
- **🤖 AI-Powered Classification**: Uses local LLMs with cloud API fallback for industry classification
- **✅ Smart Validation**: Multi-source verification and confidence scoring
- **📊 Flexible Output**: Comprehensive CSV exports with CRM-ready data fields
- **🗺️ Geographic Processing**: Intelligent state-based data collection and subdivision
- **⚙️ Configurable**: Extensive configuration options for different use cases
- **🔧 Modular Design**: Clean, maintainable architecture with pluggable components

## 📚 Documentation

- [📖 Quick Start Guide](docs/QUICK_START.md) - Get up and running in minutes
- [📋 Development Progress](docs/DEVELOPMENT_PROGRESS.md) - Current development status
- [☁️ Cloud API Setup](docs/CLOUD_API_SETUP.md) - Configure cloud AI providers
- [📊 Enhanced CRM Summary](docs/ENHANCED_CRM_SUMMARY.md) - Detailed feature overview
- [📝 Requirements](Requirements.md) - Complete project requirements
- [🔧 Development Tasks](devtasks.md) - Current development tasks and progress

## 🏗️ Development

### Requirements

- Python 3.8+
- See [requirements.txt](requirements.txt) for Python dependencies
- Optional: Local LLM setup (Ollama) for cost-effective processing

### Testing

```bash
# Run tests
python -m pytest tests/

# Run specific test
python tests/test_enhanced_app.py
```

### Scripts

- [`scripts/setup_ollama.py`](scripts/setup_ollama.py) - Setup local LLM environment
- [`scripts/run_isp_nc.py`](scripts/run_isp_nc.py) - Run ISP-specific North Carolina scraping
- [`scripts/run.py`](scripts/run.py) - Legacy run script

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

If you encounter any issues or have questions:

1. Check the [documentation](docs/)
2. Review [Requirements](Requirements.md)
3. Check [Development Tasks](devtasks.md) for known issues
4. Create an issue in the repository

---

**Note**: This project is actively under development. See [Development Progress](docs/DEVELOPMENT_PROGRESS.md) for current status. 