"""
CRM Lead Generation Agent - Main orchestrating agent.

This agent coordinates all aspects of lead generation including web scraping,
data validation, industry classification, and CSV output generation.
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

try:
    from smolagents import Tool
    SMOLAGENTS_AVAILABLE = True
except ImportError:
    SMOLAGENTS_AVAILABLE = False
    # Mock Tool class for fallback
    class Tool:
        def __init__(self, *args, **kwargs):
            pass

try:
    from langchain.tools import Tool as LangChainTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from .base_agent import BaseAgent, Task, Result, AgentFramework
from ..tools.web_scraper_tool import WebScraperTool
from ..tools.industry_classifier_tool import IndustryClassifierTool
from ..tools.data_validator_tool import DataValidatorTool
from ..tools.csv_generator_tool import CSVGeneratorTool
from ..utils.local_llm_client import LocalLLMClient

logger = logging.getLogger(__name__)

class CRMLeadGenerationAgent(BaseAgent):
    """
    Main CRM Lead Generation Agent.
    
    This agent orchestrates the complete lead generation workflow:
    1. Web scraping from multiple sources
    2. Data extraction and cleaning
    3. Industry classification using AI
    4. Data validation and quality scoring
    5. CSV output generation
    """
    
    def __init__(self):
        super().__init__(
            name="CRMLeadAgent",
            description="AI agent for comprehensive CRM lead generation",
            framework=AgentFramework.SMOL_AGENTS
        )
        
        # Initialize local LLM client for cost-effective processing
        self.llm_client = LocalLLMClient()
        
        # Initialize tools
        self._init_tools()
        
        # Initialize the agent
        self.initialize()
    
    def _init_tools(self):
        """Initialize all tools required for lead generation."""
        self.web_scraper = WebScraperTool()
        self.industry_classifier = IndustryClassifierTool(self.llm_client)
        self.data_validator = DataValidatorTool()
        self.csv_generator = CSVGeneratorTool()
        
        self.logger.info("All tools initialized successfully")
    
    def get_tools(self) -> List[Union[Tool, LangChainTool]]:
        """Get the tools available to this agent."""
        if SMOLAGENTS_AVAILABLE and self.framework == AgentFramework.SMOL_AGENTS:
            return [
                self.web_scraper.to_smol_tool(),
                self.industry_classifier.to_smol_tool(),
                self.data_validator.to_smol_tool(),
                self.csv_generator.to_smol_tool()
            ]
        elif LANGCHAIN_AVAILABLE and self.framework == AgentFramework.LANGCHAIN:
            return [
                self.web_scraper.to_langchain_tool(),
                self.industry_classifier.to_langchain_tool(),
                self.data_validator.to_langchain_tool(),
                self.csv_generator.to_langchain_tool()
            ]
        else:
            return []
    
    async def process(self, task: Task) -> Result:
        """
        Process a lead generation task.
        
        Args:
            task: Task containing search parameters
            
        Returns:
            Result with generated CSV file path and statistics
        """
        try:
            self.logger.info(f"Starting lead generation task: {task.description}")
            
            # Extract parameters
            params = task.parameters
            search_query = params.get('search_query', '')
            location = params.get('location', '')
            industry = params.get('industry', '')
            max_results = params.get('max_results', 100)
            sources = params.get('sources', ['yellow_pages', 'yelp'])
            
            # Step 1: Web scraping
            self.logger.info("Step 1: Starting web scraping")
            scraped_data = await self._scrape_business_data(
                search_query, location, industry, max_results, sources
            )
            
            if not scraped_data:
                return Result(
                    task_id=task.task_id,
                    success=False,
                    error="No data found during web scraping"
                )
            
            # Step 2: Industry classification
            self.logger.info("Step 2: Starting industry classification")
            classified_data = await self._classify_industries(scraped_data)
            
            # Step 3: Data validation
            self.logger.info("Step 3: Starting data validation")
            validated_data = await self._validate_data(classified_data)
            
            # Step 4: Generate CSV output
            self.logger.info("Step 4: Generating CSV output")
            csv_file_path = await self._generate_csv(validated_data, location)
            
            # Compile results
            result_data = {
                'csv_file_path': csv_file_path,
                'total_leads': len(validated_data),
                'high_quality_leads': len([d for d in validated_data if d.get('quality_score', 0) > 0.8]),
                'sources_used': sources,
                'processing_summary': {
                    'scraped': len(scraped_data),
                    'classified': len(classified_data),
                    'validated': len(validated_data),
                    'final_output': len(validated_data)
                }
            }
            
            self.logger.info(f"Lead generation completed successfully. Generated {len(validated_data)} leads")
            
            return Result(
                task_id=task.task_id,
                success=True,
                data=result_data,
                metadata={
                    'search_query': search_query,
                    'location': location,
                    'industry': industry,
                    'timestamp': datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            error_msg = f"Lead generation failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return Result(
                task_id=task.task_id,
                success=False,
                error=error_msg
            )
    
    async def _scrape_business_data(
        self, 
        search_query: str, 
        location: str, 
        industry: str, 
        max_results: int,
        sources: List[str]
    ) -> List[Dict[str, Any]]:
        """Scrape business data from multiple sources."""
        all_data = []
        
        for source in sources:
            try:
                self.logger.info(f"Scraping from {source}")
                
                # Use the web scraper tool
                source_data = await self.web_scraper.scrape(
                    source=source,
                    search_terms=f"{search_query} {industry}".strip(),
                    location=location,
                    max_results=max_results // len(sources)
                )
                
                if source_data:
                    # Add source attribution
                    for item in source_data:
                        item['source'] = source
                    all_data.extend(source_data)
                    
                    self.logger.info(f"Scraped {len(source_data)} records from {source}")
                else:
                    self.logger.warning(f"No data found from {source}")
                    
            except Exception as e:
                self.logger.error(f"Error scraping from {source}: {e}")
                continue
        
        # Remove duplicates based on business name and phone
        unique_data = self._deduplicate_businesses(all_data)
        
        self.logger.info(f"Total unique businesses found: {len(unique_data)}")
        return unique_data
    
    async def _classify_industries(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Classify industries for all businesses using AI."""
        classified_data = []
        
        # Process in batches for efficiency
        batch_size = 10
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            
            for business in batch:
                try:
                    # Prepare data for classification
                    classification_input = {
                        'company_name': business.get('business_name', ''),
                        'description': business.get('business_description', ''),
                        'website': business.get('website', ''),
                        'location': business.get('address', '')
                    }
                    
                    # Classify using AI
                    classification = await self.industry_classifier.classify(classification_input)
                    
                    # Add classification results to business data
                    business.update({
                        'naics_code': classification.get('naics_code'),
                        'industry_category': classification.get('industry_category'),
                        'industry_description': classification.get('industry_description'),
                        'classification_confidence': classification.get('confidence_score', 0)
                    })
                    
                    classified_data.append(business)
                    
                except Exception as e:
                    self.logger.warning(f"Classification failed for business: {e}")
                    # Add business without classification
                    business.update({
                        'naics_code': None,
                        'industry_category': 'Unknown',
                        'industry_description': 'Classification failed',
                        'classification_confidence': 0
                    })
                    classified_data.append(business)
        
        self.logger.info(f"Classified {len(classified_data)} businesses")
        return classified_data
    
    async def _validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and score data quality for all businesses."""
        validated_data = []
        
        for business in data:
            try:
                # Validate the business data
                validation_result = await self.data_validator.validate(business)
                
                # Add validation results
                business.update({
                    'quality_score': validation_result.get('quality_score', 0),
                    'validation_flags': validation_result.get('validation_flags', []),
                    'phone_valid': validation_result.get('phone_valid', False),
                    'email_valid': validation_result.get('email_valid', False),
                    'address_valid': validation_result.get('address_valid', False),
                    'website_valid': validation_result.get('website_valid', False)
                })
                
                validated_data.append(business)
                
            except Exception as e:
                self.logger.warning(f"Validation failed for business: {e}")
                # Add business with low quality score
                business.update({
                    'quality_score': 0.1,
                    'validation_flags': ['validation_error'],
                    'phone_valid': False,
                    'email_valid': False,
                    'address_valid': False,
                    'website_valid': False
                })
                validated_data.append(business)
        
        # Sort by quality score (highest first)
        validated_data.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        self.logger.info(f"Validated {len(validated_data)} businesses")
        return validated_data
    
    async def _generate_csv(self, data: List[Dict[str, Any]], location: str) -> str:
        """Generate CSV file from validated data."""
        try:
            # Generate timestamp for filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            location_clean = location.replace(' ', '_').replace(',', '')
            
            # Generate CSV
            csv_path = await self.csv_generator.generate(
                data=data,
                filename=f"leads_{timestamp}_{location_clean}.csv",
                include_metadata=True
            )
            
            self.logger.info(f"CSV generated successfully: {csv_path}")
            return csv_path
            
        except Exception as e:
            self.logger.error(f"CSV generation failed: {e}")
            raise
    
    def _deduplicate_businesses(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate businesses based on name and phone."""
        seen = set()
        unique_data = []
        
        for business in data:
            # Create a key for deduplication
            name = business.get('business_name', '').lower().strip()
            phone = business.get('phone_number', '').strip()
            
            # Use phone if available, otherwise use name
            key = phone if phone else name
            
            if key and key not in seen:
                seen.add(key)
                unique_data.append(business)
        
        self.logger.info(f"Removed {len(data) - len(unique_data)} duplicates")
        return unique_data
    
    async def generate_leads(
        self, 
        search_query: str = "",
        location: str = "",
        industry: str = "",
        max_results: int = 100,
        sources: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        High-level method to generate leads.
        
        Args:
            search_query: Business search terms
            location: Geographic location
            industry: Industry filter
            max_results: Maximum number of results
            sources: List of data sources to use
            
        Returns:
            Dictionary with results and metadata
        """
        if sources is None:
            sources = ['yellow_pages', 'yelp']
        
        # Create task
        task = Task(
            task_id=str(uuid.uuid4()),
            description=f"Generate leads for '{search_query}' in {location}",
            parameters={
                'search_query': search_query,
                'location': location,
                'industry': industry,
                'max_results': max_results,
                'sources': sources
            }
        )
        
        # Execute task
        result = await self.execute_task(task)
        
        if result.success:
            return result.data
        else:
            raise Exception(f"Lead generation failed: {result.error}")
    
    def get_supported_sources(self) -> List[str]:
        """Get list of supported data sources."""
        return ['yellow_pages', 'yelp', 'better_business_bureau']
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status and performance metrics."""
        return {
            'agent_name': self.name,
            'framework': self.framework.value,
            'status': 'active',
            'llm_status': self.llm_client.get_status(),
            'tools_status': {
                'web_scraper': 'active',
                'industry_classifier': 'active',
                'data_validator': 'active',
                'csv_generator': 'active'
            },
            'performance_stats': self.get_performance_stats()
        } 