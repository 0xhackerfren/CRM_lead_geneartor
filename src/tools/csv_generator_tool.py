"""CSV Generator Tool for CRM Lead Generation."""

import logging
import csv
import os
from datetime import datetime
from typing import Dict, Any, List

class CSVGeneratorTool:
    """CSV generator tool for creating lead output files."""
    
    def __init__(self):
        self.logger = logging.getLogger("tools.csv_generator")
        self.logger.info("CSV generator tool initialized")
        
        # Ensure output directory exists
        self.output_dir = "data/outputs"
        os.makedirs(self.output_dir, exist_ok=True)
    
    async def generate(self, data: List[Dict[str, Any]], filename: str = None, include_metadata: bool = True) -> str:
        """Generate CSV file from business data."""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"leads_{timestamp}.csv"
            
            filepath = os.path.join(self.output_dir, filename)
            
            if not data:
                self.logger.warning("No data to write to CSV")
                return filepath
            
            # Define CSV headers
            headers = [
                'company_name',
                'business_address', 
                'phone_number',
                'email_address',
                'website_url',
                'industry_naics_code',
                'industry_description',
                'business_description',
                'data_quality_score',
                'source_attribution'
            ]
            
            if include_metadata:
                headers.extend([
                    'classification_confidence',
                    'phone_valid',
                    'email_valid',
                    'address_valid',
                    'website_valid'
                ])
            
            # Write CSV file
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for business in data:
                    row = {
                        'company_name': business.get('business_name', ''),
                        'business_address': business.get('address', ''),
                        'phone_number': business.get('phone_number', ''),
                        'email_address': business.get('email_address', ''),
                        'website_url': business.get('website', ''),
                        'industry_naics_code': business.get('naics_code', ''),
                        'industry_description': business.get('industry_description', ''),
                        'business_description': business.get('business_description', ''),
                        'data_quality_score': business.get('quality_score', 0),
                        'source_attribution': business.get('source', '')
                    }
                    
                    if include_metadata:
                        row.update({
                            'classification_confidence': business.get('classification_confidence', 0),
                            'phone_valid': business.get('phone_valid', False),
                            'email_valid': business.get('email_valid', False),
                            'address_valid': business.get('address_valid', False),
                            'website_valid': business.get('website_valid', False)
                        })
                    
                    writer.writerow(row)
            
            self.logger.info(f"CSV file generated: {filepath} with {len(data)} records")
            return filepath
            
        except Exception as e:
            self.logger.error(f"CSV generation failed: {e}")
            raise
    
    def to_smol_tool(self):
        """Convert to SmolAgents tool format."""
        return None  # Placeholder
    
    def to_langchain_tool(self):
        """Convert to LangChain tool format."""
        return None  # Placeholder 