"""Data Validator Tool for CRM Lead Generation."""

import logging
import re
from typing import Dict, Any

class DataValidatorTool:
    """Data validator tool for quality scoring and validation."""
    
    def __init__(self):
        self.logger = logging.getLogger("tools.data_validator")
        self.logger.info("Data validator tool initialized")
    
    async def validate(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate business data and calculate quality score."""
        try:
            validation_results = {
                'phone_valid': self._validate_phone(business_data.get('phone_number', '')),
                'email_valid': self._validate_email(business_data.get('email_address', '')),
                'address_valid': self._validate_address(business_data.get('address', '')),
                'website_valid': self._validate_website(business_data.get('website', '')),
                'validation_flags': []
            }
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(business_data, validation_results)
            validation_results['quality_score'] = quality_score
            
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return {
                'quality_score': 0.1,
                'validation_flags': ['validation_error'],
                'phone_valid': False,
                'email_valid': False,
                'address_valid': False,
                'website_valid': False
            }
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        if not phone:
            return False
        
        # Simple phone validation
        phone_pattern = r'^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$'
        return bool(re.match(phone_pattern, phone.strip()))
    
    def _validate_email(self, email: str) -> bool:
        """Validate email address format."""
        if not email:
            return False
        
        # Simple email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(email_pattern, email.strip()))
    
    def _validate_address(self, address: str) -> bool:
        """Validate address completeness."""
        if not address:
            return False
        
        # Basic address validation - contains numbers and text
        return len(address.strip()) > 10 and any(char.isdigit() for char in address)
    
    def _validate_website(self, website: str) -> bool:
        """Validate website URL format."""
        if not website:
            return False
        
        # Simple URL validation
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(url_pattern, website.strip()))
    
    def _calculate_quality_score(self, business_data: Dict[str, Any], validation_results: Dict[str, Any]) -> float:
        """Calculate overall quality score for the business record."""
        score = 0.0
        max_score = 0.0
        
        # Required fields
        if business_data.get('business_name'):
            score += 0.3
        max_score += 0.3
        
        if business_data.get('address'):
            score += 0.2
        max_score += 0.2
        
        # Contact information
        if validation_results.get('phone_valid'):
            score += 0.2
        max_score += 0.2
        
        if validation_results.get('email_valid'):
            score += 0.1
        max_score += 0.1
        
        if validation_results.get('website_valid'):
            score += 0.1
        max_score += 0.1
        
        # Business description
        if business_data.get('business_description'):
            score += 0.1
        max_score += 0.1
        
        # Calculate final score
        final_score = (score / max_score) if max_score > 0 else 0.0
        return round(final_score, 2)
    
    def to_smol_tool(self):
        """Convert to SmolAgents tool format."""
        return None  # Placeholder
    
    def to_langchain_tool(self):
        """Convert to LangChain tool format."""
        return None  # Placeholder 