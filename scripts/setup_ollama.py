#!/usr/bin/env python3
"""
Ollama Setup and Configuration Script

This script automates the setup of Ollama for local LLM processing in the CRM
Lead Generation system, following the Local LLM Integration rule.
"""

import asyncio
import json
import logging
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import aiohttp
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OllamaSetup:
    """Ollama setup and configuration manager."""
    
    def __init__(self):
        self.ollama_url = "http://localhost:11434"
        self.required_models = [
            "llama3.1:8b-instruct-q4_K_M",
            "mistral:7b-instruct-q4_K_M"
        ]
        self.optional_models = [
            "codellama:7b-instruct",
            "phi3:mini"
        ]
        
    def check_system_requirements(self) -> Dict[str, bool]:
        """Check system requirements for Ollama."""
        requirements = {
            'os_supported': False,
            'memory_sufficient': False,
            'disk_space_sufficient': False,
            'python_version': False
        }
        
        # Check OS
        system = platform.system().lower()
        requirements['os_supported'] = system in ['windows', 'darwin', 'linux']
        
        # Check Python version
        requirements['python_version'] = sys.version_info >= (3, 9)
        
        # Check memory (rough estimate)
        try:
            import psutil
            memory_gb = psutil.virtual_memory().total / (1024**3)
            requirements['memory_sufficient'] = memory_gb >= 8
        except ImportError:
            logger.warning("psutil not available, skipping memory check")
            requirements['memory_sufficient'] = True
        
        # Check disk space
        try:
            disk_usage = os.statvfs('.')
            free_gb = (disk_usage.f_frsize * disk_usage.f_bavail) / (1024**3)
            requirements['disk_space_sufficient'] = free_gb >= 10
        except (AttributeError, OSError):
            # Windows doesn't have statvfs
            requirements['disk_space_sufficient'] = True
        
        return requirements
    
    def install_ollama(self) -> bool:
        """Install Ollama based on the operating system."""
        system = platform.system().lower()
        
        logger.info(f"Installing Ollama for {system}...")
        
        try:
            if system == 'windows':
                return self._install_ollama_windows()
            elif system == 'darwin':
                return self._install_ollama_macos()
            elif system == 'linux':
                return self._install_ollama_linux()
            else:
                logger.error(f"Unsupported operating system: {system}")
                return False
        except Exception as e:
            logger.error(f"Failed to install Ollama: {e}")
            return False
    
    def _install_ollama_windows(self) -> bool:
        """Install Ollama on Windows."""
        logger.info("Please install Ollama manually on Windows:")
        logger.info("1. Go to https://ollama.ai/download")
        logger.info("2. Download the Windows installer")
        logger.info("3. Run the installer and follow the instructions")
        logger.info("4. Restart your terminal/command prompt")
        
        input("Press Enter after installing Ollama...")
        return self.check_ollama_installation()
    
    def _install_ollama_macos(self) -> bool:
        """Install Ollama on macOS."""
        try:
            # Try using Homebrew first
            result = subprocess.run(['brew', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Installing Ollama via Homebrew...")
                result = subprocess.run(['brew', 'install', 'ollama'], check=True)
                return True
            else:
                logger.info("Homebrew not found. Please install Ollama manually:")
                logger.info("1. Go to https://ollama.ai/download")
                logger.info("2. Download the macOS installer")
                logger.info("3. Run the installer")
                input("Press Enter after installing Ollama...")
                return self.check_ollama_installation()
        except subprocess.CalledProcessError:
            logger.error("Failed to install via Homebrew")
            return False
    
    def _install_ollama_linux(self) -> bool:
        """Install Ollama on Linux."""
        try:
            logger.info("Installing Ollama on Linux...")
            
            # Download and run the install script
            install_command = "curl -fsSL https://ollama.ai/install.sh | sh"
            result = subprocess.run(install_command, shell=True, check=True)
            
            logger.info("Ollama installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Ollama: {e}")
            return False
    
    def check_ollama_installation(self) -> bool:
        """Check if Ollama is properly installed."""
        try:
            result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Ollama version: {result.stdout.strip()}")
                return True
            else:
                logger.error("Ollama not found in PATH")
                return False
        except FileNotFoundError:
            logger.error("Ollama command not found")
            return False
    
    def start_ollama_service(self) -> bool:
        """Start the Ollama service."""
        try:
            logger.info("Starting Ollama service...")
            
            # Check if already running
            if self.check_ollama_service():
                logger.info("Ollama service is already running")
                return True
            
            # Start the service
            system = platform.system().lower()
            if system == 'windows':
                # On Windows, Ollama usually starts automatically
                subprocess.Popen(['ollama', 'serve'], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                # On Unix-like systems
                subprocess.Popen(['ollama', 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Wait for service to start
            for i in range(30):  # Wait up to 30 seconds
                time.sleep(1)
                if self.check_ollama_service():
                    logger.info("Ollama service started successfully")
                    return True
            
            logger.error("Ollama service failed to start within 30 seconds")
            return False
            
        except Exception as e:
            logger.error(f"Failed to start Ollama service: {e}")
            return False
    
    def check_ollama_service(self) -> bool:
        """Check if Ollama service is running."""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    async def download_models(self, models: List[str] = None) -> Dict[str, bool]:
        """Download required models."""
        models = models or self.required_models
        results = {}
        
        for model in models:
            logger.info(f"Downloading model: {model}")
            success = await self._download_single_model(model)
            results[model] = success
            
            if success:
                logger.info(f"✅ Successfully downloaded {model}")
            else:
                logger.error(f"❌ Failed to download {model}")
        
        return results
    
    async def _download_single_model(self, model: str) -> bool:
        """Download a single model."""
        try:
            # Use subprocess to run ollama pull
            process = subprocess.Popen(
                ['ollama', 'pull', model],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor progress
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Simple progress indication
                    if 'pulling' in output.lower():
                        print(f"  {output.strip()}")
            
            return_code = process.poll()
            return return_code == 0
            
        except Exception as e:
            logger.error(f"Error downloading model {model}: {e}")
            return False
    
    def list_available_models(self) -> List[str]:
        """List models available on the system."""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                models = [line.split()[0] for line in lines if line.strip()]
                return models
            else:
                return []
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
    
    async def test_models(self, models: List[str] = None) -> Dict[str, Dict]:
        """Test models with sample prompts."""
        models = models or self.required_models
        results = {}
        
        test_prompt = "Classify this business: 'Joe's Pizza Restaurant' into an industry category."
        
        for model in models:
            logger.info(f"Testing model: {model}")
            result = await self._test_single_model(model, test_prompt)
            results[model] = result
        
        return results
    
    async def _test_single_model(self, model: str, prompt: str) -> Dict:
        """Test a single model."""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
                
                start_time = time.time()
                
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'response_time': response_time,
                            'response': result.get('response', '')[:100] + '...',
                            'tokens': result.get('eval_count', 0)
                        }
                    else:
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}",
                            'response_time': response_time
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response_time': 0
            }
    
    def create_config_file(self) -> bool:
        """Create Ollama configuration for the CRM system."""
        try:
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            ollama_config = {
                "ollama": {
                    "base_url": self.ollama_url,
                    "models": {
                        "primary": self.required_models[0],
                        "backup": self.required_models[1] if len(self.required_models) > 1 else self.required_models[0],
                        "available": self.list_available_models()
                    },
                    "settings": {
                        "timeout": 30,
                        "max_retries": 3,
                        "temperature": 0.1
                    }
                }
            }
            
            config_file = config_dir / "ollama_config.json"
            with open(config_file, 'w') as f:
                json.dump(ollama_config, f, indent=2)
            
            logger.info(f"Configuration saved to {config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create config file: {e}")
            return False

async def main():
    """Main setup function."""
    print("🤖 CRM Lead Generator - Ollama Setup")
    print("=" * 50)
    
    setup = OllamaSetup()
    
    # Check system requirements
    print("\n📋 Checking system requirements...")
    requirements = setup.check_system_requirements()
    
    for req, status in requirements.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {req.replace('_', ' ').title()}: {status}")
    
    if not all(requirements.values()):
        print("\n❌ System requirements not met. Please address the issues above.")
        return False
    
    # Check if Ollama is installed
    print("\n🔍 Checking Ollama installation...")
    if not setup.check_ollama_installation():
        print("Ollama not found. Installing...")
        if not setup.install_ollama():
            print("❌ Failed to install Ollama")
            return False
    else:
        print("✅ Ollama is already installed")
    
    # Start Ollama service
    print("\n🚀 Starting Ollama service...")
    if not setup.start_ollama_service():
        print("❌ Failed to start Ollama service")
        return False
    
    # Download required models
    print("\n📥 Downloading required models...")
    print("This may take several minutes depending on your internet connection...")
    
    download_results = await setup.download_models()
    
    failed_downloads = [model for model, success in download_results.items() if not success]
    if failed_downloads:
        print(f"❌ Failed to download models: {failed_downloads}")
        return False
    
    # Test models
    print("\n🧪 Testing models...")
    test_results = await setup.test_models()
    
    for model, result in test_results.items():
        if result['success']:
            print(f"  ✅ {model}: {result['response_time']:.2f}s")
        else:
            print(f"  ❌ {model}: {result['error']}")
    
    # Create configuration
    print("\n⚙️ Creating configuration...")
    if setup.create_config_file():
        print("✅ Configuration created successfully")
    else:
        print("❌ Failed to create configuration")
        return False
    
    print("\n🎉 Ollama setup completed successfully!")
    print("\nNext steps:")
    print("1. The CRM system will now use local LLM processing")
    print("2. Run 'python main_app.py' to start the application")
    print("3. Check the Gradio interface for AI-powered lead generation")
    
    return True

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed with error: {e}")
        sys.exit(1) 