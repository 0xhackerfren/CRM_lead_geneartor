"""
Data Validator

Validates and enhances business data quality, including standardization,
validation checks, and quality scoring.
"""

import re
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class DataValidator:
    """Validator for business data quality and enhancement."""
    
    def __init__(self):
        """Initialize data validator."""
        self.email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        self.phone_pattern = re.compile(r'^\(\d{3}\) \d{3}-\d{4}$')
        self.url_pattern = re.compile(r'^https?://.+\..+')
    
    def validate_and_enhance(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and enhance business data.
        
        Args:
            business_data: Raw business data dictionary
            
        Returns:
            Enhanced and validated business data
        """
        enhanced_data = business_data.copy()
        
        try:
            # Validate and standardize core fields
            enhanced_data = self._validate_core_fields(enhanced_data)
            
            # Validate contact information
            enhanced_data = self._validate_contact_info(enhanced_data)
            
            # Calculate quality scores
            enhanced_data = self._calculate_quality_scores(enhanced_data)
            
            # Add validation metadata
            enhanced_data = self._add_validation_metadata(enhanced_data)
            
        except Exception as e:
            logger.error(f"Error validating business data: {e}")
        
        return enhanced_data
    
    def _validate_core_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean core business fields."""
        validated = data.copy()
        
        # Business name validation
        business_name = validated.get('business_name', '').strip()
        if business_name:
            # Clean up business name
            validated['business_name'] = self._clean_business_name(business_name)
        else:
            validated['business_name'] = 'UNKNOWN'
        
        # Address validation and parsing
        address = validated.get('address', '').strip()
        if address:
            parsed_address = self._parse_address(address)
            validated.update(parsed_address)
        
        # Business description cleaning
        description = validated.get('business_description', '').strip()
        if description:
            validated['business_description'] = self._clean_description(description)
        
        return validated
    
    def _validate_contact_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and standardize contact information."""
        validated = data.copy()
        
        # Phone number validation
        phone = validated.get('phone_number', '')
        if phone and phone != 'NOT_FOUND':
            validated['phone_number'] = self._validate_phone(phone)
        
        # Email validation
        email_fields = ['ceo_email', 'general_email', 'sales_email', 'support_email']
        for field in email_fields:
            email = validated.get(field, '')
            if email and email != 'NOT_FOUND':
                validated[field] = self._validate_email(email)
        
        # Website validation
        website = validated.get('website', '')
        if website and website != 'NOT_FOUND':
            validated['website'] = self._validate_website(website)
        
        return validated
    
    def _calculate_quality_scores(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate various quality scores for the data."""
        enhanced = data.copy()
        
        # Data completeness score (percentage of non-empty fields)
        total_fields = 50  # Expected number of important fields
        completed_fields = sum(1 for value in data.values() 
                             if value and str(value).strip() and value != 'NOT_FOUND')
        completeness_score = min(100, int((completed_fields / total_fields) * 100))
        enhanced['completeness_score'] = completeness_score
        
        # Confidence score (data quality and reliability)
        confidence_score = self._calculate_confidence_score(data)
        enhanced['confidence_score'] = confidence_score
        
        # Overall data quality score
        quality_score = self._calculate_overall_quality_score(data)
        enhanced['data_quality_score'] = quality_score
        
        # Lead score (sales potential)
        lead_score = self._calculate_lead_score(data)
        enhanced['lead_score'] = lead_score
        
        return enhanced
    
    def _calculate_confidence_score(self, data: Dict[str, Any]) -> int:
        """Calculate confidence score based on data validation."""
        score = 10  # Start with maximum
        
        # Deduct points for missing critical information
        if not data.get('business_name') or data.get('business_name') == 'UNKNOWN':
            score -= 3
        
        if not data.get('phone_number') or data.get('phone_number') == 'NOT_FOUND':
            score -= 2
        
        if not data.get('address') or data.get('address') == 'NOT_FOUND':
            score -= 2
        
        if not data.get('website') or data.get('website') == 'NOT_FOUND':
            score -= 1
        
        # Add points for enhanced contact information
        if data.get('ceo_name') and data.get('ceo_name') != 'NOT_FOUND':
            score += 1
        
        if data.get('ceo_email') and data.get('ceo_email') != 'NOT_FOUND':
            score += 1
        
        return max(1, min(10, score))
    
    def _calculate_overall_quality_score(self, data: Dict[str, Any]) -> int:
        """Calculate overall data quality score."""
        score = 0
        
        # Core business information (40% of score)
        if data.get('business_name') and data.get('business_name') != 'UNKNOWN':
            score += 2
        if data.get('business_description'):
            score += 1
        if data.get('industry') or data.get('industry_primary'):
            score += 1
        
        # Contact information (30% of score)
        if data.get('phone_number') and data.get('phone_number') != 'NOT_FOUND':
            score += 1
        if data.get('address') and data.get('address') != 'NOT_FOUND':
            score += 1
        if data.get('website') and data.get('website') != 'NOT_FOUND':
            score += 1
        
        # Enhanced contact information (30% of score)
        if data.get('ceo_name') and data.get('ceo_name') != 'NOT_FOUND':
            score += 1
        if data.get('ceo_email') and data.get('ceo_email') != 'NOT_FOUND':
            score += 1
        if data.get('general_email') and data.get('general_email') != 'NOT_FOUND':
            score += 1
        
        return min(10, score)
    
    def _calculate_lead_score(self, data: Dict[str, Any]) -> int:
        """Calculate lead scoring for sales potential."""
        score = 5  # Base score
        
        # Company size indicators
        if data.get('company_size'):
            score += 1
        
        # Technology/service indicators
        if data.get('service_type') or data.get('technology_focus'):
            score += 1
        
        # Contact accessibility
        if data.get('ceo_email') and data.get('ceo_email') != 'NOT_FOUND':
            score += 2
        elif data.get('general_email') and data.get('general_email') != 'NOT_FOUND':
            score += 1
        
        # Website presence
        if data.get('website') and data.get('website') != 'NOT_FOUND':
            score += 1
        
        return min(10, score)
    
    def _clean_business_name(self, name: str) -> str:
        """Clean and standardize business name."""
        # Remove extra whitespace
        cleaned = ' '.join(name.split())
        
        # Standardize common business suffixes
        suffixes = {
            ' inc.': ' Inc.',
            ' llc': ' LLC',
            ' corp.': ' Corp.',
            ' ltd.': ' Ltd.',
            ' co.': ' Co.'
        }
        
        for old, new in suffixes.items():
            cleaned = cleaned.replace(old, new)
            cleaned = cleaned.replace(old.title(), new)
        
        return cleaned
    
    def _parse_address(self, address: str) -> Dict[str, str]:
        """Parse address into components."""
        parsed = {}
        
        # Simple address parsing (can be enhanced)
        if address and address != 'NOT_FOUND':
            parsed['headquarters_address'] = address
            
            # Try to extract city, state, zip
            # This is a basic implementation - could be enhanced with proper address parsing
            parts = address.split(',')
            if len(parts) >= 2:
                parsed['headquarters_city'] = parts[-2].strip()
                
                # Look for state and zip in last part
                last_part = parts[-1].strip()
                state_zip_match = re.search(r'([A-Z]{2})\s+(\d{5})', last_part)
                if state_zip_match:
                    parsed['headquarters_state'] = state_zip_match.group(1)
                    parsed['headquarters_zip'] = state_zip_match.group(2)
        
        return parsed
    
    def _clean_description(self, description: str) -> str:
        """Clean business description."""
        # Remove extra whitespace and normalize
        cleaned = ' '.join(description.split())
        
        # Limit length
        if len(cleaned) > 500:
            cleaned = cleaned[:497] + '...'
        
        return cleaned
    
    def _validate_phone(self, phone: str) -> str:
        """Validate and standardize phone number."""
        if not phone or phone == 'NOT_FOUND':
            return 'NOT_FOUND'
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # Format as (XXX) XXX-XXXX if 10 digits
        if len(digits) == 10:
            formatted = f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            return formatted if self.phone_pattern.match(formatted) else phone
        elif len(digits) == 11 and digits[0] == '1':
            formatted = f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
            return formatted if self.phone_pattern.match(formatted) else phone
        else:
            return phone  # Return original if can't standardize
    
    def _validate_email(self, email: str) -> str:
        """Validate email address format."""
        if not email or email == 'NOT_FOUND':
            return 'NOT_FOUND'
        
        email = email.strip().lower()
        
        if self.email_pattern.match(email):
            return email
        else:
            return 'INVALID_EMAIL'
    
    def _validate_website(self, website: str) -> str:
        """Validate and standardize website URL."""
        if not website or website == 'NOT_FOUND':
            return 'NOT_FOUND'
        
        website = website.strip()
        
        # Add https:// if no protocol specified
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        # Basic URL validation
        if self.url_pattern.match(website):
            return website
        else:
            return 'INVALID_URL'
    
    def _add_validation_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add validation metadata to the record."""
        enhanced = data.copy()
        
        # Add validation timestamp
        enhanced['validation_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Add validation status
        quality_score = enhanced.get('data_quality_score', 0)
        if quality_score >= 8:
            enhanced['validation_status'] = 'high_quality'
        elif quality_score >= 6:
            enhanced['validation_status'] = 'good_quality'
        elif quality_score >= 4:
            enhanced['validation_status'] = 'acceptable_quality'
        else:
            enhanced['validation_status'] = 'needs_review'
        
        return enhanced 