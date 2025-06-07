"""
CSV Generator

Generates comprehensive CSV files with CRM-ready fields including
enhanced contact information and business intelligence data.
"""

import csv
import os
import logging
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class CSVGenerator:
    """Generator for CRM-optimized CSV files."""
    
    def __init__(self):
        """Initialize CSV generator."""
        self.output_dir = os.path.join('data', 'outputs')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_csv(
        self, 
        data: List[Dict[str, Any]], 
        query: str, 
        location: str,
        filename_prefix: str = "crm_leads"
    ) -> str:
        """
        Generate comprehensive CSV file for CRM system.
        
        Args:
            data: List of business data dictionaries
            query: Search query used
            location: Geographic location
            filename_prefix: Prefix for filename
            
        Returns:
            Path to generated CSV file
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            query_slug = self._slugify(query)
            location_slug = self._slugify(location)
            
            filename = f"{filename_prefix}_{query_slug}_{location_slug}_{timestamp}.csv"
            filepath = os.path.join(self.output_dir, filename)
            
            # Define comprehensive field set
            fieldnames = self._get_comprehensive_fieldnames()
            
            # Write CSV file
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for business in data:
                    row = self._prepare_csv_row(business, fieldnames)
                    writer.writerow(row)
            
            logger.info(f"Generated CSV file: {filepath} with {len(data)} records")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating CSV: {e}")
            return ""
    
    def _get_comprehensive_fieldnames(self) -> List[str]:
        """Get comprehensive list of CRM fields."""
        return [
            # Core Company Information
            'business_name', 'dba_name', 'company_type', 'industry_primary',
            'industry_secondary', 'business_description', 'founded_date',
            'company_size', 'annual_revenue', 'public_private',
            
            # Contact Information
            'headquarters_address', 'headquarters_city', 'headquarters_state',
            'headquarters_zip', 'phone_main', 'phone_toll_free', 'fax_number',
            'email_general', 'website_url', 'linkedin_company',
            
            # Executive Leadership
            'ceo_name', 'ceo_email', 'ceo_linkedin', 'president_name',
            'cfo_name', 'cto_name', 'sales_director', 'marketing_director',
            'hr_director',
            
            # Additional Contact Information
            'general_email', 'sales_email', 'support_email',
            'procurement_contact', 'it_contact', 'finance_contact',
            
            # Business Intelligence
            'market_position', 'main_competitors', 'competitive_advantages',
            'geographic_coverage', 'customer_base', 'revenue_growth',
            
            # Technology Information
            'service_type', 'technology_focus', 'coverage',
            'primary_software', 'crm_system', 'cloud_provider',
            
            # Operational Details
            'business_hours', 'time_zone', 'certifications',
            'licenses', 'union_status',
            
            # Sales Intelligence
            'buying_cycle', 'budget_range', 'fiscal_year_end',
            'procurement_process', 'vendor_requirements',
            
            # Additional Metrics
            'rating', 'review_count', 'social_media_presence',
            
            # Data Quality Metadata
            'data_quality_score', 'completeness_score', 'confidence_score',
            'verification_status', 'data_source', 'data_sources_all',
            'collection_date', 'last_updated', 'naics_code',
            
            # Lead Scoring
            'lead_score', 'buying_intent', 'timing_indicators',
            'budget_indicators', 'authority_level', 'need_urgency'
        ]
    
    def _prepare_csv_row(self, business: Dict[str, Any], fieldnames: List[str]) -> Dict[str, Any]:
        """
        Prepare a business record for CSV output.
        
        Args:
            business: Business data dictionary
            fieldnames: List of expected field names
            
        Returns:
            CSV-ready row dictionary
        """
        row = {}
        
        for field in fieldnames:
            value = business.get(field, 'NOT_FOUND')
            
            # Handle special field mappings
            if field == 'headquarters_address' and value == 'NOT_FOUND':
                value = business.get('address', 'NOT_FOUND')
            elif field == 'phone_main' and value == 'NOT_FOUND':
                value = business.get('phone_number', 'NOT_FOUND')
            elif field == 'website_url' and value == 'NOT_FOUND':
                value = business.get('website', 'NOT_FOUND')
            elif field == 'industry_primary' and value == 'NOT_FOUND':
                value = business.get('industry', 'NOT_FOUND')
            elif field == 'collection_date' and value == 'NOT_FOUND':
                value = datetime.now().strftime('%Y-%m-%d')
            elif field == 'last_updated' and value == 'NOT_FOUND':
                value = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elif field == 'verification_status' and value == 'NOT_FOUND':
                value = 'auto_extracted'
            
            # Clean and standardize the value
            row[field] = self._clean_field_value(value, field)
        
        return row
    
    def _clean_field_value(self, value: Any, field_name: str) -> str:
        """
        Clean and standardize field values.
        
        Args:
            value: Raw field value
            field_name: Name of the field
            
        Returns:
            Cleaned value as string
        """
        if value is None or value == '' or value == 'None':
            return 'NOT_FOUND'
        
        # Convert to string
        str_value = str(value).strip()
        
        # Field-specific cleaning
        if 'email' in field_name.lower():
            # Validate email format
            if '@' in str_value and '.' in str_value:
                return str_value.lower()
            else:
                return 'NOT_FOUND' if str_value in ['NOT_FOUND', ''] else str_value
        
        elif 'phone' in field_name.lower():
            # Standardize phone numbers
            if str_value and str_value != 'NOT_FOUND':
                return self._standardize_phone(str_value)
            return 'NOT_FOUND'
        
        elif 'website' in field_name.lower() or 'url' in field_name.lower():
            # Standardize URLs
            if str_value and str_value != 'NOT_FOUND':
                return self._standardize_url(str_value)
            return 'NOT_FOUND'
        
        elif field_name.endswith('_score'):
            # Ensure scores are numeric
            try:
                return str(max(0, min(10, int(float(str_value)))))
            except (ValueError, TypeError):
                return '0'
        
        # Default cleaning
        return str_value if str_value else 'NOT_FOUND'
    
    def _standardize_phone(self, phone: str) -> str:
        """Standardize phone number format."""
        if not phone or phone == 'NOT_FOUND':
            return 'NOT_FOUND'
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # Format as (XXX) XXX-XXXX if 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone  # Return original if can't standardize
    
    def _standardize_url(self, url: str) -> str:
        """Standardize URL format."""
        if not url or url == 'NOT_FOUND':
            return 'NOT_FOUND'
        
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    def _slugify(self, text: str) -> str:
        """Convert text to filename-safe slug."""
        if not text:
            return 'unknown'
        
        # Replace spaces and special characters
        slug = text.lower().replace(' ', '_').replace('/', '_').replace(',', '')
        
        # Remove any remaining problematic characters
        safe_chars = 'abcdefghijklmnopqrstuvwxyz0123456789_-'
        slug = ''.join(c for c in slug if c in safe_chars)
        
        return slug[:50]  # Limit length 