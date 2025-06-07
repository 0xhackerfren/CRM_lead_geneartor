"""
Configuration management for CRM Lead Generation AI Agent.

This module handles loading, validation, and access to application configuration
following the hierarchical configuration pattern from our rules.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AgentConfig(BaseModel):
    """Configuration for AI agents."""
    primary_framework: str = "smol_agents"
    fallback_framework: str = "langchain"
    
    class SmolAgentsConfig(BaseModel):
        model: str = "Qwen/Qwen2.5-72B-Instruct"
        planning_interval: int = 3
        max_iterations: int = 10
        temperature: float = 0.1
        max_tokens: int = 2000
    
    class LangChainConfig(BaseModel):
        model_name: str = "microsoft/DialoGPT-medium"
        memory_type: str = "conversation_buffer"
        max_memory_length: int = 10
    
    smol_agents: SmolAgentsConfig = SmolAgentsConfig()
    langchain: LangChainConfig = LangChainConfig()

class LocalLLMConfig(BaseModel):
    """Configuration for local LLM integration."""
    enabled: bool = True
    platform: str = "ollama"
    primary_model: str = "llama3.1:8b-instruct-q4_K_M"
    backup_model: str = "mistral:7b-instruct-q4_K_M"
    max_response_time: float = 5.0
    max_retries: int = 3
    base_url: str = "http://localhost:11434"

class ScrapingConfig(BaseModel):
    """Configuration for web scraping."""
    rate_limit: float = 2.0
    max_retries: int = 3
    timeout: int = 30
    respect_robots_txt: bool = True
    user_agents: list = Field(default_factory=lambda: [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    ])

class OutputConfig(BaseModel):
    """Configuration for output generation."""
    format: str = "csv"
    include_metadata: bool = True
    include_quality_scores: bool = True
    max_records_per_file: int = 10000
    output_directory: str = "data/outputs"
    filename_template: str = "leads_{timestamp}_{location}.csv"
    fields: list = Field(default_factory=lambda: [
        "company_name", "business_address", "phone_number", "email_address",
        "website_url", "industry_naics_code", "industry_description",
        "business_description", "data_quality_score", "source_attribution"
    ])

class GradioConfig(BaseModel):
    """Configuration for Gradio frontend."""
    host: str = "127.0.0.1"
    port: int = 7860
    share: bool = False
    auth: Optional[list] = None
    theme: str = "default"
    title: str = "CRM Lead Generation AI Agent"
    description: str = "Generate high-quality business leads using AI agents"

class AppConfig(BaseModel):
    """Main application configuration."""
    name: str = "CRM Lead Generator"
    version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"

class CRMConfig(BaseModel):
    """Complete CRM application configuration."""
    app: AppConfig = AppConfig()
    agents: AgentConfig = AgentConfig()
    local_llm: LocalLLMConfig = LocalLLMConfig()
    scraping: ScrapingConfig = ScrapingConfig()
    output: OutputConfig = OutputConfig()
    gradio: GradioConfig = GradioConfig()
    
    @validator('*', pre=True)
    def resolve_env_vars(cls, v):
        """Resolve environment variables in configuration values."""
        if isinstance(v, str) and v.startswith('${') and v.endswith('}'):
            env_var = v[2:-1]
            return os.getenv(env_var, v)
        return v

class ConfigManager:
    """
    Configuration manager with hierarchical loading.
    
    Follows the configuration management rule:
    1. Default settings (built-in defaults)
    2. Configuration files (YAML)
    3. Environment variables (override)
    4. Runtime parameters (command-line overrides)
    """
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_file()
        self._config: Optional[CRMConfig] = None
        self.load_config()
    
    def _find_config_file(self) -> str:
        """Find the configuration file using standard locations."""
        possible_paths = [
            "config/config.yaml",
            "config.yaml",
            os.path.expanduser("~/.crm/config.yaml"),
            "/etc/crm/config.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        # Return default path if none found
        return "config/config.yaml"
    
    def load_config(self) -> None:
        """Load configuration from file with error handling."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                self._config = CRMConfig(**config_data)
            else:
                print(f"Warning: Config file not found at {self.config_path}, using defaults")
                self._config = CRMConfig()
                
        except Exception as e:
            print(f"Error loading config: {e}")
            print("Using default configuration")
            self._config = CRMConfig()
    
    @property
    def config(self) -> CRMConfig:
        """Get the current configuration."""
        if self._config is None:
            self.load_config()
        return self._config
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key_path: Dot-separated path to config value (e.g., 'agents.smol_agents.model')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
            
        Example:
            >>> config.get('agents.smol_agents.model')
            'Qwen/Qwen2.5-72B-Instruct'
        """
        try:
            value = self.config
            for key in key_path.split('.'):
                if hasattr(value, key):
                    value = getattr(value, key)
                else:
                    return default
            return value
        except Exception:
            return default
    
    def update(self, key_path: str, value: Any) -> None:
        """
        Update configuration value at runtime.
        
        Args:
            key_path: Dot-separated path to config value
            value: New value to set
        """
        # Implementation for runtime configuration updates
        # This would update the in-memory configuration
        pass
    
    def validate(self) -> bool:
        """
        Validate the current configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            # Validate required directories exist
            output_dir = Path(self.config.output.output_directory)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Validate log directory
            log_dir = Path("logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            
            # Validate cache directory
            cache_dir = Path("data/cache")
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            return True
            
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return self.config.dict()
    
    def save(self, path: Optional[str] = None) -> None:
        """Save current configuration to file."""
        save_path = path or self.config_path
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        with open(save_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, indent=2)

# Global configuration instance
_config_manager: Optional[ConfigManager] = None

def get_config() -> CRMConfig:
    """Get the global configuration instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.config

def init_config(config_path: Optional[str] = None) -> ConfigManager:
    """Initialize the global configuration manager."""
    global _config_manager
    _config_manager = ConfigManager(config_path)
    return _config_manager

# Environment-specific overrides
def get_env_config_overrides() -> Dict[str, Any]:
    """Get configuration overrides from environment variables."""
    overrides = {}
    
    # API Keys
    if os.getenv('OPENAI_API_KEY'):
        overrides['fallback_apis.openai.enabled'] = True
        
    if os.getenv('ANTHROPIC_API_KEY'):
        overrides['fallback_apis.anthropic.enabled'] = True
    
    # Ollama configuration
    if os.getenv('OLLAMA_HOST'):
        overrides['local_llm.base_url'] = os.getenv('OLLAMA_HOST')
    
    # Debug mode
    if os.getenv('DEBUG'):
        overrides['app.debug'] = os.getenv('DEBUG').lower() == 'true'
    
    return overrides 