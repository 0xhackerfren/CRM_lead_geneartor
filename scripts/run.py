#!/usr/bin/env python3
"""
CRM Lead Generation AI Agent - Run Script

This script handles setup verification and launches the application
with comprehensive error handling and helpful guidance.
"""

import sys
import os
import subprocess
import logging
from pathlib import Path

def setup_logging():
    """Setup basic logging for the run script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_python_version():
    """Verify Python version compatibility."""
    if sys.version_info < (3, 9):
        raise RuntimeError(
            f"Python 3.9+ required. Current version: {sys.version_info.major}.{sys.version_info.minor}"
        )

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'gradio',
        'pydantic', 
        'pyyaml',
        'aiohttp',
        'beautifulsoup4',
        'pandas'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        raise RuntimeError(
            f"Missing required packages: {', '.join(missing_packages)}\n"
            "Please run: pip install -r requirements.txt"
        )

def check_ollama_availability():
    """Check if Ollama is available and running."""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def create_directories():
    """Create necessary directories if they don't exist."""
    directories = [
        'data/outputs',
        'data/cache', 
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

def display_startup_info(logger, ollama_available):
    """Display helpful startup information."""
    logger.info("🚀 Starting CRM Lead Generation AI Agent")
    logger.info("=" * 50)
    
    logger.info(f"✅ Python version: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    logger.info("✅ Dependencies: All required packages installed")
    logger.info("✅ Directories: Created successfully")
    
    if ollama_available:
        logger.info("✅ Ollama: Available and running")
        logger.info("   → Local LLM processing enabled")
    else:
        logger.warning("⚠️  Ollama: Not available")
        logger.warning("   → Will use fallback processing")
        logger.warning("   → Install Ollama for better performance and privacy:")
        logger.warning("   → https://ollama.ai")
    
    logger.info("=" * 50)
    logger.info("🌐 Application will be available at: http://localhost:7860")
    logger.info("📖 Check README.md for complete documentation")
    logger.info("🛟 For support, check logs/crm_agent.log")
    logger.info("=" * 50)

def main():
    """Main run script entry point."""
    logger = setup_logging()
    
    try:
        # Pre-flight checks
        logger.info("Performing pre-flight checks...")
        
        check_python_version()
        check_dependencies()
        create_directories()
        
        # Check Ollama availability
        ollama_available = check_ollama_availability()
        
        # Display startup information
        display_startup_info(logger, ollama_available)
        
        # Import and run the main application
        logger.info("Loading application...")
        
        # Add the current directory to Python path
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        # Import and run the app
        from app import main as app_main
        app_main()
        
    except KeyboardInterrupt:
        logger.info("\n👋 Application stopped by user")
        sys.exit(0)
        
    except RuntimeError as e:
        logger.error(f"❌ Setup Error: {e}")
        logger.error("\nPlease fix the above issues and try again.")
        logger.error("For help, check the README.md file or documentation.")
        sys.exit(1)
        
    except ImportError as e:
        logger.error(f"❌ Import Error: {e}")
        logger.error("\nThis might indicate missing dependencies.")
        logger.error("Try running: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Unexpected Error: {e}")
        logger.error("\nPlease check the logs for more details.")
        logger.error("If the problem persists, please report it as an issue.")
        sys.exit(1)

if __name__ == "__main__":
    main() 