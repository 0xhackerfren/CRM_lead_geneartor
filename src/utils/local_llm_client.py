"""
Local LLM Client for cost-effective AI processing.

This module provides a client for local LLM models (Ollama) with automatic
fallback to cloud APIs when needed, implementing the Local LLM Integration rule.
"""

import asyncio
import logging
import aiohttp
import json
import os
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import time

try:
    from ..config.settings import get_config
except ImportError:
    # Fallback to config manager
    from .config_manager import config_manager
    def get_config():
        return config_manager.get_config()

logger = logging.getLogger(__name__)

class LocalLLMClient:
    """
    Local LLM client with cloud API fallback.
    
    Prioritizes local processing for cost-effectiveness and privacy,
    with automatic fallback to cloud APIs when local models fail.
    """
    
    def __init__(self):
        self.config = get_config()
        
        # Handle both pydantic and dict config formats
        if hasattr(self.config, 'local_llm'):
            self.llm_config = self.config.local_llm
        else:
            # Convert dict to object-like access
            class ConfigObject:
                def __init__(self, data):
                    for key, value in data.items():
                        if isinstance(value, dict):
                            setattr(self, key, ConfigObject(value))
                        else:
                            setattr(self, key, value)
            
            llm_config_dict = self.config.get('local_llm', {})
            self.llm_config = ConfigObject(llm_config_dict)
        
        # Performance tracking
        self.stats = {
            'total_requests': 0,
            'local_successes': 0,
            'cloud_fallbacks': 0,
            'total_errors': 0,
            'average_response_time': 0,
            'last_local_success': None,
            'last_cloud_fallback': None
        }
        
        # Session for HTTP requests
        self.session: Optional[aiohttp.ClientSession] = None
        
        platform = getattr(self.llm_config, 'platform', 'ollama') if hasattr(self.llm_config, 'platform') else 'ollama'
        logger.info(f"LocalLLMClient initialized - Platform: {platform}")
    
    async def _ensure_session(self):
        """Ensure HTTP session is available."""
        if self.session is None or self.session.closed:
            max_response_time = getattr(self.llm_config, 'max_response_time', 30.0) if hasattr(self.llm_config, 'max_response_time') else 30.0
            timeout = aiohttp.ClientTimeout(total=max_response_time)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def _check_local_llm_availability(self) -> bool:
        """Check if local LLM service is available."""
        try:
            await self._ensure_session()
            
            platform = getattr(self.llm_config, 'platform', 'ollama') if hasattr(self.llm_config, 'platform') else 'ollama'
            if platform == "ollama":
                # Check Ollama service
                base_url = getattr(self.llm_config, 'base_url', 'http://localhost:11434') if hasattr(self.llm_config, 'base_url') else 'http://localhost:11434'
                async with self.session.get(f"{base_url}/api/tags") as response:
                    return response.status == 200
            
            return False
            
        except Exception as e:
            logger.debug(f"Local LLM unavailable: {e}")
            return False
    
    async def _call_local_llm(self, prompt: str, model: str = None) -> Dict[str, Any]:
        """Call local LLM (Ollama)."""
        primary_model = getattr(self.llm_config, 'primary_model', 'llama3.1:8b-instruct-q4_K_M') if hasattr(self.llm_config, 'primary_model') else 'llama3.1:8b-instruct-q4_K_M'
        model = model or primary_model
        
        try:
            await self._ensure_session()
            
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "max_tokens": 1000
                }
            }
            
            start_time = time.time()
            
            base_url = getattr(self.llm_config, 'base_url', 'http://localhost:11434') if hasattr(self.llm_config, 'base_url') else 'http://localhost:11434'
            async with self.session.post(
                f"{base_url}/api/generate",
                json=payload
            ) as response:
                
                response_time = time.time() - start_time
                
                if response.status == 200:
                    result = await response.json()
                    
                    return {
                        'success': True,
                        'response': result.get('response', ''),
                        'model': model,
                        'source': 'local',
                        'response_time': response_time,
                        'tokens_used': result.get('eval_count', 0)
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"Local LLM error: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.warning(f"Local LLM call failed: {e}")
            
            # Try backup model if primary failed
            if model == primary_model:
                logger.info("Trying backup local model...")
                backup_model = getattr(self.llm_config, 'backup_model', 'mistral:7b-instruct-q4_K_M') if hasattr(self.llm_config, 'backup_model') else 'mistral:7b-instruct-q4_K_M'
                return await self._call_local_llm(prompt, backup_model)
            
            raise e
    
    async def _call_cloud_api(self, prompt: str, provider: str = "openai") -> Dict[str, Any]:
        """Call cloud API as fallback."""
        start_time = time.time()
        
        try:
            logger.info(f"Using cloud API fallback: {provider}")
            
            # Get API configuration
            if hasattr(self.config, 'fallback_apis'):
                fallback_config = self.config.fallback_apis
                openai_config = fallback_config.openai
                anthropic_config = fallback_config.anthropic
            else:
                fallback_config_dict = self.config.get('fallback_apis', {})
                # Convert dict to object-like access
                class ConfigObject:
                    def __init__(self, data):
                        for key, value in data.items():
                            if isinstance(value, dict):
                                setattr(self, key, ConfigObject(value))
                            else:
                                setattr(self, key, value)
                
                openai_config = ConfigObject(fallback_config_dict.get('openai', {}))
                anthropic_config = ConfigObject(fallback_config_dict.get('anthropic', {}))
            
            if provider == "openai":
                return await self._call_openai_api(prompt, openai_config, start_time)
            elif provider == "anthropic":
                return await self._call_anthropic_api(prompt, anthropic_config, start_time)
            else:
                raise ValueError(f"Unsupported provider: {provider}")
                
        except Exception as e:
            logger.error(f"Cloud API call failed: {e}")
            raise e
    
    async def _call_openai_api(self, prompt: str, config, start_time: float) -> Dict[str, Any]:
        """Call OpenAI API."""
        enabled = getattr(config, 'enabled', False) if hasattr(config, 'enabled') else config.get('enabled', False)
        if not enabled:
            raise Exception("OpenAI API is disabled in configuration")
        
        # Get API key from environment or config
        api_key = os.getenv('OPENAI_API_KEY') or getattr(config, 'api_key', None)
        if not api_key:
            raise Exception("OpenAI API key not found in environment or configuration")
        
        await self._ensure_session()
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        model = getattr(config, 'model', 'gpt-4o-mini') if hasattr(config, 'model') else config.get('model', 'gpt-4o-mini')
        max_tokens = getattr(config, 'max_tokens', 1000) if hasattr(config, 'max_tokens') else config.get('max_tokens', 1000)
        temperature = getattr(config, 'temperature', 0.1) if hasattr(config, 'temperature') else config.get('temperature', 0.1)
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        async with self.session.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload
        ) as response:
            
            response_time = time.time() - start_time
            
            if response.status == 200:
                result = await response.json()
                
                return {
                    'success': True,
                    'response': result['choices'][0]['message']['content'],
                    'model': model,
                    'source': 'openai',
                    'response_time': response_time,
                    'tokens_used': result['usage']['total_tokens']
                }
            else:
                error_text = await response.text()
                raise Exception(f"OpenAI API error: {response.status} - {error_text}")
    
    async def _call_anthropic_api(self, prompt: str, config, start_time: float) -> Dict[str, Any]:
        """Call Anthropic API."""
        enabled = getattr(config, 'enabled', False) if hasattr(config, 'enabled') else config.get('enabled', False)
        if not enabled:
            raise Exception("Anthropic API is disabled in configuration")
        
        # Get API key from environment or config
        api_key = os.getenv('ANTHROPIC_API_KEY') or getattr(config, 'api_key', None)
        if not api_key:
            raise Exception("Anthropic API key not found in environment or configuration")
        
        await self._ensure_session()
        
        headers = {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        model = getattr(config, 'model', 'claude-3-haiku-20240307') if hasattr(config, 'model') else config.get('model', 'claude-3-haiku-20240307')
        max_tokens = getattr(config, 'max_tokens', 1000) if hasattr(config, 'max_tokens') else config.get('max_tokens', 1000)
        
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        async with self.session.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload
        ) as response:
            
            response_time = time.time() - start_time
            
            if response.status == 200:
                result = await response.json()
                
                return {
                    'success': True,
                    'response': result['content'][0]['text'],
                    'model': model,
                    'source': 'anthropic',
                    'response_time': response_time,
                    'tokens_used': result['usage']['input_tokens'] + result['usage']['output_tokens']
                }
            else:
                error_text = await response.text()
                raise Exception(f"Anthropic API error: {response.status} - {error_text}")
    
    async def generate_text(
        self, 
        prompt: str, 
        max_retries: int = None,
        force_cloud: bool = False
    ) -> Dict[str, Any]:
        """
        Generate text using local LLM with cloud fallback.
        
        Args:
            prompt: Text prompt for generation
            max_retries: Maximum retry attempts (default: from config)
            force_cloud: Force use of cloud API
            
        Returns:
            Dict with response, metadata, and source information
        """
        start_time = time.time()
        max_retries = max_retries or self.llm_config.max_retries
        
        self.stats['total_requests'] += 1
        
        # Try local LLM first (unless forced to use cloud)
        if not force_cloud and self.llm_config.enabled:
            for attempt in range(max_retries):
                try:
                    # Check availability
                    if await self._check_local_llm_availability():
                        result = await self._call_local_llm(prompt)
                        
                        if result['success']:
                            self.stats['local_successes'] += 1
                            self.stats['last_local_success'] = datetime.now()
                            self._update_response_time(time.time() - start_time)
                            
                            logger.info(f"Local LLM success in {result['response_time']:.2f}s")
                            return result
                    
                except Exception as e:
                    logger.warning(f"Local LLM attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # Fallback to cloud APIs
        cloud_providers = []
        
        # Determine available cloud providers
        if hasattr(self.config, 'fallback_apis'):
            fallback_config = self.config.fallback_apis
            if fallback_config.openai.enabled:
                cloud_providers.append("openai")
            if fallback_config.anthropic.enabled:
                cloud_providers.append("anthropic")
        else:
            fallback_config_dict = self.config.get('fallback_apis', {})
            openai_config = fallback_config_dict.get('openai', {})
            anthropic_config = fallback_config_dict.get('anthropic', {})
            
            if openai_config.get('enabled', False):
                cloud_providers.append("openai")
            if anthropic_config.get('enabled', False):
                cloud_providers.append("anthropic")
        
        for provider in cloud_providers:
            try:
                logger.info(f"Falling back to {provider} API")
                result = await self._call_cloud_api(prompt, provider)
                
                if result['success']:
                    self.stats['cloud_fallbacks'] += 1
                    self.stats['last_cloud_fallback'] = datetime.now()
                    self._update_response_time(time.time() - start_time)
                    
                    logger.info(f"{provider} API success in {result['response_time']:.2f}s")
                    return result
                    
            except Exception as e:
                logger.warning(f"{provider} API fallback failed: {e}")
                continue
        
        # All attempts failed
        self.stats['total_errors'] += 1
        
        return {
            'success': False,
            'error': 'All LLM attempts failed',
            'response': '',
            'model': 'none',
            'source': 'error',
            'response_time': time.time() - start_time
        }
    
    async def classify_industry(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify business industry using LLM.
        
        Args:
            business_info: Dictionary with business information
            
        Returns:
            Classification result with NAICS code and confidence
        """
        business_name = business_info.get('company_name', '')
        business_desc = business_info.get('business_description', '')
        business_address = business_info.get('business_address', '')
        
        prompt = f"""
Classify the following business into the most appropriate NAICS (North American Industry Classification System) code.

Business Information:
- Name: {business_name}
- Description: {business_desc}
- Address: {business_address}

Please provide:
1. The 6-digit NAICS code
2. Industry description
3. Confidence score (0-100)
4. Brief reasoning

Format your response as JSON:
{{
    "naics_code": "123456",
    "industry_description": "Industry Name",
    "confidence_score": 85,
    "reasoning": "Brief explanation"
}}
"""
        
        result = await self.generate_text(prompt)
        
        if result['success']:
            try:
                # Try to parse JSON response
                response_text = result['response'].strip()
                
                # Extract JSON if wrapped in markdown
                if '```json' in response_text:
                    start = response_text.find('```json') + 7
                    end = response_text.find('```', start)
                    response_text = response_text[start:end].strip()
                elif '```' in response_text:
                    start = response_text.find('```') + 3
                    end = response_text.find('```', start)
                    response_text = response_text[start:end].strip()
                
                classification = json.loads(response_text)
                
                return {
                    'success': True,
                    'naics_code': classification.get('naics_code', '000000'),
                    'industry_description': classification.get('industry_description', 'Unknown'),
                    'confidence_score': classification.get('confidence_score', 0),
                    'reasoning': classification.get('reasoning', ''),
                    'source': result['source'],
                    'model': result['model']
                }
                
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse LLM classification response: {e}")
                
                # Fallback: try to extract basic info
                response_text = result['response']
                naics_code = "000000"
                confidence = 50
                
                # Simple regex to find 6-digit codes
                import re
                naics_match = re.search(r'\b\d{6}\b', response_text)
                if naics_match:
                    naics_code = naics_match.group()
                
                return {
                    'success': True,
                    'naics_code': naics_code,
                    'industry_description': 'Classification with low confidence',
                    'confidence_score': confidence,
                    'reasoning': 'Parsed from unstructured response',
                    'source': result['source'],
                    'model': result['model']
                }
        
        return {
            'success': False,
            'naics_code': '000000',
            'industry_description': 'Classification failed',
            'confidence_score': 0,
            'reasoning': 'LLM call failed',
            'error': result.get('error', 'Unknown error')
        }
    
    def _update_response_time(self, response_time: float):
        """Update average response time."""
        if self.stats['average_response_time'] == 0:
            self.stats['average_response_time'] = response_time
        else:
            # Moving average
            total_requests = self.stats['total_requests']
            current_avg = self.stats['average_response_time']
            self.stats['average_response_time'] = (
                (current_avg * (total_requests - 1) + response_time) / total_requests
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        total = self.stats['total_requests']
        
        return {
            'total_requests': total,
            'local_success_rate': (self.stats['local_successes'] / total * 100) if total > 0 else 0,
            'cloud_fallback_rate': (self.stats['cloud_fallbacks'] / total * 100) if total > 0 else 0,
            'error_rate': (self.stats['total_errors'] / total * 100) if total > 0 else 0,
            'average_response_time': self.stats['average_response_time'],
            'last_local_success': self.stats['last_local_success'],
            'last_cloud_fallback': self.stats['last_cloud_fallback'],
            'local_llm_enabled': getattr(self.llm_config, 'enabled', True) if hasattr(self.llm_config, 'enabled') else True,
            'primary_model': getattr(self.llm_config, 'primary_model', 'llama3.1:8b-instruct-q4_K_M') if hasattr(self.llm_config, 'primary_model') else 'llama3.1:8b-instruct-q4_K_M',
            'platform': getattr(self.llm_config, 'platform', 'ollama') if hasattr(self.llm_config, 'platform') else 'ollama'
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on local and cloud services."""
        results = {
            'local_llm': {'available': False, 'response_time': None, 'error': None},
            'cloud_api': {'available': False, 'response_time': None, 'error': None}
        }
        
        # Test local LLM
        try:
            start_time = time.time()
            available = await self._check_local_llm_availability()
            response_time = time.time() - start_time
            
            results['local_llm'] = {
                'available': available,
                'response_time': response_time,
                'error': None if available else 'Service not responding'
            }
        except Exception as e:
            results['local_llm'] = {
                'available': False,
                'response_time': None,
                'error': str(e)
            }
        
        # Test cloud API (simplified check)
        try:
            # Check if any cloud APIs are configured
            cloud_providers = []
            if hasattr(self.config, 'fallback_apis'):
                fallback_config = self.config.fallback_apis
                if fallback_config.openai.enabled:
                    cloud_providers.append("openai")
                if fallback_config.anthropic.enabled:
                    cloud_providers.append("anthropic")
            else:
                fallback_config_dict = self.config.get('fallback_apis', {})
                openai_config = fallback_config_dict.get('openai', {})
                anthropic_config = fallback_config_dict.get('anthropic', {})
                
                if openai_config.get('enabled', False):
                    cloud_providers.append("openai")
                if anthropic_config.get('enabled', False):
                    cloud_providers.append("anthropic")
            
            if cloud_providers:
                start_time = time.time()
                test_result = await self._call_cloud_api("test", cloud_providers[0])
                response_time = time.time() - start_time
                
                results['cloud_api'] = {
                    'available': test_result['success'],
                    'response_time': response_time,
                    'error': None if test_result['success'] else 'API not responding'
                }
            else:
                results['cloud_api'] = {
                    'available': False,
                    'response_time': None,
                    'error': 'No cloud APIs configured'
                }
        except Exception as e:
            results['cloud_api'] = {
                'available': False,
                'response_time': None,
                'error': str(e)
            }
        
        return results
    
    async def close(self):
        """Clean up resources."""
        if self.session and not self.session.closed:
            await self.session.close()
        
        logger.info("LocalLLMClient session closed") 