"""
Configuration Manager for Runtime Updates

This module handles runtime configuration updates, especially for API keys
and other sensitive settings that users may want to configure through the frontend.
"""

import os
import json
import yaml
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigurationManager:
    """
    Manages runtime configuration updates and secure credential storage.
    """
    
    def __init__(self):
        self.config_cache = {}
        self.runtime_config = {}
        self.config_file_path = None
        self.load_current_config()
    
    def load_current_config(self):
        """Load current configuration from file system."""
        try:
            # Determine which config file to load
            env = os.getenv('CRM_ENV', 'development')
            config_dir = Path('config')
            
            # Try environment-specific config first
            env_config_file = config_dir / f"{env}.yaml"
            if env_config_file.exists():
                self.config_file_path = env_config_file
            else:
                self.config_file_path = config_dir / "config.yaml"
            
            if self.config_file_path.exists():
                with open(self.config_file_path, 'r') as f:
                    self.config_cache = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {self.config_file_path}")
            else:
                logger.warning("No configuration file found, using defaults")
                self.config_cache = self._get_default_config()
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config_cache = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'app': {
                'name': 'CRM Lead Generator',
                'version': '1.0.0',
                'debug': True
            },
            'local_llm': {
                'enabled': True,
                'platform': 'ollama',
                'primary_model': 'llama3.1:8b-instruct-q4_K_M',
                'backup_model': 'mistral:7b-instruct-q4_K_M'
            },
            'fallback_apis': {
                'openai': {
                    'enabled': False,
                    'model': 'gpt-4o-mini',
                    'max_tokens': 1000,
                    'temperature': 0.1
                },
                'anthropic': {
                    'enabled': False,
                    'model': 'claude-3-haiku-20240307',
                    'max_tokens': 1000
                }
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration with runtime overrides applied."""
        # Start with base config
        config = self.config_cache.copy()
        
        # Apply runtime overrides
        config = self._deep_merge(config, self.runtime_config)
        
        # Apply environment variable overrides
        config = self._apply_env_overrides(config)
        
        return config
    
    def update_api_keys(self, openai_key: str = None, anthropic_key: str = None) -> Dict[str, Any]:
        """
        Update API keys and enable/disable providers accordingly.
        
        Args:
            openai_key: OpenAI API key
            anthropic_key: Anthropic API key
            
        Returns:
            Updated configuration status
        """
        result = {
            'success': True,
            'updates': [],
            'errors': []
        }
        
        try:
            # Update OpenAI configuration
            if openai_key is not None:
                if openai_key.strip():
                    # Set environment variable (secure storage)
                    os.environ['OPENAI_API_KEY'] = openai_key.strip()
                    
                    # Enable OpenAI in runtime config
                    if 'fallback_apis' not in self.runtime_config:
                        self.runtime_config['fallback_apis'] = {}
                    if 'openai' not in self.runtime_config['fallback_apis']:
                        self.runtime_config['fallback_apis']['openai'] = {}
                    
                    self.runtime_config['fallback_apis']['openai']['enabled'] = True
                    result['updates'].append('OpenAI API enabled')
                    logger.info("OpenAI API key updated and enabled")
                else:
                    # Disable OpenAI
                    if 'OPENAI_API_KEY' in os.environ:
                        del os.environ['OPENAI_API_KEY']
                    
                    if 'fallback_apis' in self.runtime_config and 'openai' in self.runtime_config['fallback_apis']:
                        self.runtime_config['fallback_apis']['openai']['enabled'] = False
                    
                    result['updates'].append('OpenAI API disabled')
                    logger.info("OpenAI API key removed and disabled")
            
            # Update Anthropic configuration
            if anthropic_key is not None:
                if anthropic_key.strip():
                    # Set environment variable (secure storage)
                    os.environ['ANTHROPIC_API_KEY'] = anthropic_key.strip()
                    
                    # Enable Anthropic in runtime config
                    if 'fallback_apis' not in self.runtime_config:
                        self.runtime_config['fallback_apis'] = {}
                    if 'anthropic' not in self.runtime_config['fallback_apis']:
                        self.runtime_config['fallback_apis']['anthropic'] = {}
                    
                    self.runtime_config['fallback_apis']['anthropic']['enabled'] = True
                    result['updates'].append('Anthropic API enabled')
                    logger.info("Anthropic API key updated and enabled")
                else:
                    # Disable Anthropic
                    if 'ANTHROPIC_API_KEY' in os.environ:
                        del os.environ['ANTHROPIC_API_KEY']
                    
                    if 'fallback_apis' in self.runtime_config and 'anthropic' in self.runtime_config['fallback_apis']:
                        self.runtime_config['fallback_apis']['anthropic']['enabled'] = False
                    
                    result['updates'].append('Anthropic API disabled')
                    logger.info("Anthropic API key removed and disabled")
                    
        except Exception as e:
            error_msg = f"Error updating API keys: {e}"
            result['errors'].append(error_msg)
            result['success'] = False
            logger.error(error_msg)
        
        return result
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get current API configuration status."""
        config = self.get_config()
        fallback_apis = config.get('fallback_apis', {})
        
        return {
            'openai': {
                'enabled': fallback_apis.get('openai', {}).get('enabled', False),
                'has_key': bool(os.getenv('OPENAI_API_KEY')),
                'model': fallback_apis.get('openai', {}).get('model', 'gpt-4o-mini')
            },
            'anthropic': {
                'enabled': fallback_apis.get('anthropic', {}).get('enabled', False),
                'has_key': bool(os.getenv('ANTHROPIC_API_KEY')),
                'model': fallback_apis.get('anthropic', {}).get('model', 'claude-3-haiku-20240307')
            },
            'local_llm': {
                'enabled': config.get('local_llm', {}).get('enabled', True),
                'platform': config.get('local_llm', {}).get('platform', 'ollama'),
                'primary_model': config.get('local_llm', {}).get('primary_model', 'llama3.1:8b-instruct-q4_K_M')
            }
        }
    
    def test_api_connection(self, provider: str) -> Dict[str, Any]:
        """
        Test API connection for a specific provider.
        
        Args:
            provider: 'openai' or 'anthropic'
            
        Returns:
            Test result
        """
        result = {
            'success': False,
            'provider': provider,
            'message': '',
            'response_time': 0
        }
        
        try:
            import asyncio
            from ..utils.local_llm_client import LocalLLMClient
            
            async def test_connection():
                client = LocalLLMClient()
                test_prompt = "Hello, this is a test. Please respond with 'API connection successful'."
                
                start_time = datetime.now()
                response = await client._call_cloud_api(test_prompt, provider)
                end_time = datetime.now()
                
                await client.close()
                
                result['response_time'] = (end_time - start_time).total_seconds()
                
                if response['success']:
                    result['success'] = True
                    result['message'] = f"{provider.title()} API connection successful"
                    logger.info(f"{provider} API test successful")
                else:
                    result['message'] = f"{provider.title()} API test failed: {response.get('error', 'Unknown error')}"
                    logger.warning(f"{provider} API test failed")
                
                return result
            
            # Run the async test
            return asyncio.run(test_connection())
            
        except Exception as e:
            result['message'] = f"{provider.title()} API test error: {str(e)}"
            logger.error(f"{provider} API test error: {e}")
            return result
    
    def update_local_llm_config(self, enabled: bool = None, model: str = None) -> Dict[str, Any]:
        """Update local LLM configuration."""
        result = {
            'success': True,
            'updates': [],
            'errors': []
        }
        
        try:
            if 'local_llm' not in self.runtime_config:
                self.runtime_config['local_llm'] = {}
            
            if enabled is not None:
                self.runtime_config['local_llm']['enabled'] = enabled
                status = "enabled" if enabled else "disabled"
                result['updates'].append(f'Local LLM {status}')
                logger.info(f"Local LLM {status}")
            
            if model is not None:
                self.runtime_config['local_llm']['primary_model'] = model
                result['updates'].append(f'Primary model set to {model}')
                logger.info(f"Primary model updated to {model}")
                
        except Exception as e:
            error_msg = f"Error updating local LLM config: {e}"
            result['errors'].append(error_msg)
            result['success'] = False
            logger.error(error_msg)
        
        return result
    
    def save_runtime_config(self, filename: str = None) -> Dict[str, Any]:
        """Save current runtime configuration to a file."""
        try:
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"runtime_config_{timestamp}.yaml"
            
            config_dir = Path('config')
            config_dir.mkdir(exist_ok=True)
            
            config_file = config_dir / filename
            
            # Merge base config with runtime overrides
            full_config = self._deep_merge(self.config_cache.copy(), self.runtime_config)
            
            with open(config_file, 'w') as f:
                yaml.dump(full_config, f, default_flow_style=False, indent=2)
            
            logger.info(f"Runtime configuration saved to {config_file}")
            
            return {
                'success': True,
                'filename': str(config_file),
                'message': f'Configuration saved to {filename}'
            }
            
        except Exception as e:
            error_msg = f"Error saving configuration: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def reset_runtime_config(self) -> Dict[str, Any]:
        """Reset runtime configuration to defaults."""
        try:
            self.runtime_config.clear()
            
            # Clear API keys from environment
            for key in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
                if key in os.environ:
                    del os.environ[key]
            
            logger.info("Runtime configuration reset to defaults")
            
            return {
                'success': True,
                'message': 'Configuration reset to defaults'
            }
            
        except Exception as e:
            error_msg = f"Error resetting configuration: {e}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Apply environment variable overrides."""
        # This is a simplified version - in production you'd want more sophisticated env var mapping
        env_mappings = {
            'CRM_LOCAL_LLM_ENABLED': ('local_llm', 'enabled'),
            'CRM_SCRAPING_RATE_LIMIT': ('scraping', 'rate_limit'),
            'CRM_DEBUG': ('app', 'debug')
        }
        
        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                if section not in config:
                    config[section] = {}
                
                # Convert string values to appropriate types
                if value.lower() in ('true', 'false'):
                    config[section][key] = value.lower() == 'true'
                elif value.replace('.', '').isdigit():
                    config[section][key] = float(value) if '.' in value else int(value)
                else:
                    config[section][key] = value
        
        return config

# Global configuration manager instance
config_manager = ConfigurationManager() 