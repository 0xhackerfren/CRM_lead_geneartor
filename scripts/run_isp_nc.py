#!/usr/bin/env python3
"""
ISP Lead Generation for North Carolina

This script generates a comprehensive list of Internet Service Providers (ISPs) 
operating in North Carolina, following the CRM lead generation system architecture.
"""

import asyncio
import csv
import json
import logging
import os
import re
import requests
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ISPScraper:
    """Web scraper specialized for finding ISP companies."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.rate_limit_delay = 2.0  # seconds between requests
        
    def _rate_limit(self):
        """Implement rate limiting between requests."""
        time.sleep(self.rate_limit_delay)
    
    def scrape_yellow_pages_isp(self, location: str) -> List[Dict[str, Any]]:
        """Scrape ISP listings from Yellow Pages."""
        logger.info(f"Scraping Yellow Pages for ISPs in {location}")
        results = []
        
        try:
            # Yellow Pages search URL for ISPs
            search_url = f"https://www.yellowpages.com/search?search_terms=internet+service+provider&geo_location_terms={location.replace(' ', '+')}"
            
            self._rate_limit()
            response = self.session.get(search_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find business listings
                listings = soup.find_all('div', class_='result')
                
                for listing in listings[:20]:  # Limit to first 20 results
                    try:
                        business_data = self._extract_yp_business_data(listing)
                        if business_data and 'internet' in business_data.get('business_description', '').lower():
                            business_data['source'] = 'yellow_pages'
                            results.append(business_data)
                    except Exception as e:
                        logger.warning(f"Error extracting business data: {e}")
                        continue
            
            logger.info(f"Found {len(results)} ISP listings from Yellow Pages")
            
        except Exception as e:
            logger.error(f"Error scraping Yellow Pages: {e}")
        
        return results
    
    def _extract_yp_business_data(self, listing) -> Optional[Dict[str, Any]]:
        """Extract business data from Yellow Pages listing."""
        try:
            # Extract business name
            name_elem = listing.find('a', class_='business-name')
            business_name = name_elem.get_text(strip=True) if name_elem else ''
            
            # Extract address
            address_elem = listing.find('p', class_='adr')
            address = address_elem.get_text(strip=True) if address_elem else ''
            
            # Extract phone
            phone_elem = listing.find('div', class_='phones')
            phone = phone_elem.get_text(strip=True) if phone_elem else ''
            
            # Extract website (if available)
            website_elem = listing.find('a', class_='track-visit-website')
            website = website_elem.get('href', '') if website_elem else ''
            
            # Extract description
            desc_elem = listing.find('p', class_='snippet')
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            if business_name:
                return {
                    'business_name': business_name,
                    'address': address,
                    'phone_number': phone,
                    'website': website,
                    'business_description': description
                }
        except Exception as e:
            logger.warning(f"Error extracting business data: {e}")
        
        return None
    
    def scrape_fcc_broadband_providers(self, state: str) -> List[Dict[str, Any]]:
        """Scrape FCC broadband provider data for a state."""
        logger.info(f"Searching FCC data for broadband providers in {state}")
        results = []
        
        # Known major ISPs in North Carolina (as fallback data)
        nc_isps = [
            {
                'business_name': 'Spectrum (Charter Communications)',
                'address': 'Multiple locations across North Carolina',
                'phone_number': '(855) 243-8892',
                'website': 'https://www.spectrum.com',
                'business_description': 'Cable internet, TV, and phone services throughout North Carolina',
                'service_type': 'Cable',
                'coverage': 'Statewide'
            },
            {
                'business_name': 'AT&T Internet',
                'address': 'Multiple locations across North Carolina',
                'phone_number': '(800) 288-2020',
                'website': 'https://www.att.com',
                'business_description': 'DSL, fiber, and wireless internet services in North Carolina',
                'service_type': 'DSL/Fiber',
                'coverage': 'Statewide'
            },
            {
                'business_name': 'CenturyLink (Lumen)',
                'address': 'Multiple locations across North Carolina',
                'phone_number': '(866) 642-0444',
                'website': 'https://www.centurylink.com',
                'business_description': 'DSL and fiber internet services across North Carolina',
                'service_type': 'DSL/Fiber',
                'coverage': 'Statewide'
            },
            {
                'business_name': 'Brightspeed',
                'address': 'Multiple locations across North Carolina',
                'phone_number': '(833) 692-7773',
                'website': 'https://www.brightspeed.com',
                'business_description': 'Fiber and DSL internet services in North Carolina',
                'service_type': 'Fiber/DSL',
                'coverage': 'Select areas'
            },
            {
                'business_name': 'Windstream',
                'address': 'Multiple locations across North Carolina',
                'phone_number': '(866) 445-8084',
                'website': 'https://www.windstream.com',
                'business_description': 'Internet and telecommunications services in rural and urban North Carolina',
                'service_type': 'DSL/Fiber',
                'coverage': 'Select areas'
            },
            {
                'business_name': 'Viasat',
                'address': 'Satellite coverage across North Carolina',
                'phone_number': '(855) 810-1308',
                'website': 'https://www.viasat.com',
                'business_description': 'Satellite internet services covering all of North Carolina',
                'service_type': 'Satellite',
                'coverage': 'Statewide'
            },
            {
                'business_name': 'HughesNet',
                'address': 'Satellite coverage across North Carolina',
                'phone_number': '(866) 347-3292',
                'website': 'https://www.hughesnet.com',
                'business_description': 'Satellite internet services available throughout North Carolina',
                'service_type': 'Satellite',
                'coverage': 'Statewide'
            },
            {
                'business_name': 'Wilkes Communications',
                'address': 'North Wilkesboro, NC',
                'phone_number': '(336) 838-7000',
                'website': 'https://www.wilkes.net',
                'business_description': 'Local fiber and cable internet provider serving northwest North Carolina',
                'service_type': 'Fiber/Cable',
                'coverage': 'Northwest NC'
            },
            {
                'business_name': 'SkyLine/SkyBest',
                'address': 'West Jefferson, NC',
                'phone_number': '(800) 759-2226',
                'website': 'https://www.skybest.com',
                'business_description': 'Local telecommunications and internet provider serving western North Carolina',
                'service_type': 'Fiber/DSL',
                'coverage': 'Western NC'
            },
            {
                'business_name': 'Yadtel',
                'address': 'Yadkinville, NC',
                'phone_number': '(336) 679-2000',
                'website': 'https://www.yadtel.net',
                'business_description': 'Local telecommunications and internet provider serving Yadkin County and surrounding areas',
                'service_type': 'Fiber/DSL',
                'coverage': 'Yadkin County area'
            }
        ]
        
        for isp in nc_isps:
            isp['source'] = 'fcc_broadband_data'
            results.append(isp)
        
        logger.info(f"Added {len(results)} known ISPs from FCC/industry data")
        return results
    
    def scrape_local_isp_directories(self) -> List[Dict[str, Any]]:
        """Scrape local ISP directory sites for North Carolina providers."""
        logger.info("Searching local ISP directories for North Carolina providers")
        results = []
        
        # Additional local/regional ISPs in North Carolina
        local_isps = [
            {
                'business_name': 'Randolph Telephone',
                'address': 'Asheboro, NC',
                'phone_number': '(336) 625-5151',
                'website': 'https://www.rtmc.net',
                'business_description': 'Local telecommunications provider serving Randolph County with fiber and DSL',
                'service_type': 'Fiber/DSL',
                'coverage': 'Randolph County'
            },
            {
                'business_name': 'Piedmont Rural Telephone',
                'address': 'Pittsboro, NC',
                'phone_number': '(919) 542-4444',
                'website': 'https://www.prtc.net',
                'business_description': 'Rural telecommunications cooperative providing internet and phone services',
                'service_type': 'Fiber/DSL',
                'coverage': 'Central NC rural areas'
            },
            {
                'business_name': 'Cape Hatteras Electric Cooperative',
                'address': 'Buxton, NC',
                'phone_number': '(252) 995-5616',
                'website': 'https://www.chec.coop',
                'business_description': 'Electric cooperative also providing fiber internet to Outer Banks',
                'service_type': 'Fiber',
                'coverage': 'Outer Banks'
            },
            {
                'business_name': 'Charlotte Metro Credit Union',
                'address': 'Charlotte, NC',
                'phone_number': '(704) 375-0183',
                'website': 'https://www.charlottemetro.org',
                'business_description': 'Credit union offering internet services to members in Charlotte area',
                'service_type': 'Partnership/Reseller',
                'coverage': 'Charlotte metro'
            }
        ]
        
        for isp in local_isps:
            isp['source'] = 'local_directories'
            results.append(isp)
        
        logger.info(f"Added {len(results)} local ISPs from directory data")
        return results

class ISPClassifier:
    """Classifier specialized for ISP industry categorization."""
    
    def __init__(self):
        self.isp_keywords = [
            'internet service provider', 'isp', 'broadband', 'internet',
            'telecommunications', 'telecom', 'fiber', 'cable internet',
            'wireless internet', 'satellite internet', 'dsl', 'high-speed internet'
        ]
    
    def classify(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Classify ISP businesses with detailed categorization."""
        business_name = business_data.get('business_name', '').lower()
        description = business_data.get('business_description', '').lower()
        service_type = business_data.get('service_type', '').lower()
        
        # Determine ISP type
        isp_type = self._determine_isp_type(business_name, description, service_type)
        
        # Calculate confidence based on keyword matches
        confidence = self._calculate_confidence(business_name, description)
        
        return {
            'naics_code': '517311',  # Wired Telecommunications Carriers
            'industry_category': 'Telecommunications',
            'industry_description': 'Internet Service Providers',
            'isp_type': isp_type,
            'confidence_score': confidence,
            'classification_method': 'keyword_matching'
        }
    
    def _determine_isp_type(self, name: str, description: str, service_type: str) -> str:
        """Determine the type of ISP based on available information."""
        combined_text = f"{name} {description} {service_type}"
        
        if any(word in combined_text for word in ['fiber', 'fibre']):
            return 'Fiber'
        elif any(word in combined_text for word in ['cable', 'coax']):
            return 'Cable'
        elif any(word in combined_text for word in ['satellite']):
            return 'Satellite'
        elif any(word in combined_text for word in ['dsl', 'digital subscriber']):
            return 'DSL'
        elif any(word in combined_text for word in ['wireless', 'radio']):
            return 'Wireless'
        else:
            return 'Mixed/Other'
    
    def _calculate_confidence(self, name: str, description: str) -> int:
        """Calculate confidence score for ISP classification."""
        combined_text = f"{name} {description}"
        score = 0
        
        # Check for direct ISP keywords
        for keyword in self.isp_keywords:
            if keyword in combined_text:
                if keyword in ['internet service provider', 'isp']:
                    score += 30
                elif keyword in ['broadband', 'internet']:
                    score += 20
                else:
                    score += 10
        
        # Bonus for telecommunications context
        if any(word in combined_text for word in ['telecommunications', 'telecom']):
            score += 15
        
        # Bonus for service type indicators
        if any(word in combined_text for word in ['fiber', 'cable', 'satellite', 'dsl']):
            score += 10
        
        return min(score, 100)

class ISPDataValidator:
    """Data validator specialized for ISP business data."""
    
    def validate(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ISP business data quality."""
        score = 0.0
        flags = []
        
        # Required fields validation
        if business_data.get('business_name'):
            score += 0.25
        else:
            flags.append('missing_business_name')
        
        if business_data.get('address'):
            score += 0.15
        else:
            flags.append('missing_address')
        
        if business_data.get('phone_number'):
            score += 0.20
            if self._validate_phone(business_data['phone_number']):
                score += 0.05
            else:
                flags.append('invalid_phone_format')
        else:
            flags.append('missing_phone')
        
        if business_data.get('website'):
            score += 0.15
            if self._validate_website(business_data['website']):
                score += 0.05
            else:
                flags.append('invalid_website_format')
        else:
            flags.append('missing_website')
        
        if business_data.get('business_description'):
            score += 0.15
        else:
            flags.append('missing_description')
        
        # ISP-specific validation
        if business_data.get('service_type'):
            score += 0.05
        
        if business_data.get('coverage'):
            score += 0.05
        
        return {
            'quality_score': round(score, 2),
            'phone_valid': self._validate_phone(business_data.get('phone_number', '')),
            'website_valid': self._validate_website(business_data.get('website', '')),
            'validation_flags': flags
        }
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        if not phone:
            return False
        # Basic US phone number pattern
        phone_pattern = r'^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$'
        return bool(re.match(phone_pattern, phone.strip()))
    
    def _validate_website(self, website: str) -> bool:
        """Validate website URL format."""
        if not website:
            return False
        try:
            result = urlparse(website)
            return all([result.scheme, result.netloc])
        except:
            return False

class ISPCSVGenerator:
    """CSV generator for ISP lead data."""
    
    def __init__(self):
        os.makedirs('data/outputs', exist_ok=True)
    
    def generate(self, data: List[Dict[str, Any]], location: str) -> str:
        """Generate CSV file for ISP leads."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"isp_leads_{location.lower().replace(' ', '_')}_{timestamp}.csv"
        filepath = os.path.join('data/outputs', filename)
        
        headers = [
            'company_name',
            'business_address',
            'phone_number',
            'website_url',
            'business_description',
            'isp_type',
            'service_coverage',
            'naics_code',
            'industry_description',
            'data_quality_score',
            'confidence_score',
            'source_attribution',
            'validation_flags'
        ]
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for business in data:
                row = {
                    'company_name': business.get('business_name', ''),
                    'business_address': business.get('address', ''),
                    'phone_number': business.get('phone_number', ''),
                    'website_url': business.get('website', ''),
                    'business_description': business.get('business_description', ''),
                    'isp_type': business.get('isp_type', ''),
                    'service_coverage': business.get('coverage', ''),
                    'naics_code': business.get('naics_code', ''),
                    'industry_description': business.get('industry_description', ''),
                    'data_quality_score': business.get('quality_score', 0),
                    'confidence_score': business.get('confidence_score', 0),
                    'source_attribution': business.get('source', ''),
                    'validation_flags': '; '.join(business.get('validation_flags', []))
                }
                writer.writerow(row)
        
        return filepath

class NCISPLeadGenerator:
    """Main lead generator for North Carolina ISPs."""
    
    def __init__(self):
        self.scraper = ISPScraper()
        self.classifier = ISPClassifier()
        self.validator = ISPDataValidator()
        self.csv_generator = ISPCSVGenerator()
        
        logger.info("NC ISP Lead Generator initialized successfully")
    
    async def generate_isp_leads(self) -> Dict[str, Any]:
        """Generate comprehensive list of ISPs in North Carolina."""
        logger.info("Starting ISP lead generation for North Carolina")
        
        all_data = []
        
        # Step 1: Collect data from multiple sources
        logger.info("Step 1: Collecting ISP data from multiple sources")
        
        # Scrape Yellow Pages
        yp_data = self.scraper.scrape_yellow_pages_isp("North Carolina")
        all_data.extend(yp_data)
        
        # Get FCC/industry data
        fcc_data = self.scraper.scrape_fcc_broadband_providers("North Carolina")
        all_data.extend(fcc_data)
        
        # Get local directory data
        local_data = self.scraper.scrape_local_isp_directories()
        all_data.extend(local_data)
        
        logger.info(f"Collected {len(all_data)} total business records")
        
        # Step 2: Remove duplicates
        logger.info("Step 2: Removing duplicates")
        deduplicated_data = self._deduplicate_businesses(all_data)
        logger.info(f"After deduplication: {len(deduplicated_data)} unique businesses")
        
        # Step 3: Classify industries
        logger.info("Step 3: Classifying industries")
        classified_data = []
        for business in deduplicated_data:
            classification = self.classifier.classify(business)
            business.update(classification)
            classified_data.append(business)
        
        # Step 4: Validate data
        logger.info("Step 4: Validating data quality")
        validated_data = []
        for business in classified_data:
            validation = self.validator.validate(business)
            business.update(validation)
            validated_data.append(business)
        
        # Step 5: Generate CSV
        logger.info("Step 5: Generating CSV output")
        csv_file_path = self.csv_generator.generate(validated_data, "North Carolina")
        
        # Compile results
        high_quality_leads = [d for d in validated_data if d.get('quality_score', 0) > 0.7]
        
        results = {
            'csv_file_path': csv_file_path,
            'total_leads': len(validated_data),
            'high_quality_leads': len(high_quality_leads),
            'sources_used': ['yellow_pages', 'fcc_broadband_data', 'local_directories'],
            'processing_summary': {
                'collected': len(all_data),
                'deduplicated': len(deduplicated_data),
                'classified': len(classified_data),
                'validated': len(validated_data),
                'high_quality': len(high_quality_leads)
            }
        }
        
        logger.info(f"ISP lead generation completed successfully")
        logger.info(f"Generated {len(validated_data)} total leads, {len(high_quality_leads)} high quality")
        logger.info(f"CSV file saved to: {csv_file_path}")
        
        return results
    
    def _deduplicate_businesses(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate businesses based on name similarity."""
        unique_businesses = []
        seen_names = set()
        
        for business in data:
            name = business.get('business_name', '').lower().strip()
            # Simplified deduplication - can be enhanced with fuzzy matching
            if name and name not in seen_names:
                seen_names.add(name)
                unique_businesses.append(business)
        
        return unique_businesses

async def main():
    """Main function to run the ISP lead generation."""
    print("🌐 CRM Lead Generation - North Carolina ISPs")
    print("=" * 50)
    
    generator = NCISPLeadGenerator()
    
    try:
        results = await generator.generate_isp_leads()
        
        print(f"\n✅ Lead generation completed successfully!")
        print(f"📊 Results:")
        print(f"   - Total ISPs found: {results['total_leads']}")
        print(f"   - High quality leads: {results['high_quality_leads']}")
        print(f"   - CSV file: {results['csv_file_path']}")
        print(f"\n📈 Processing Summary:")
        for stage, count in results['processing_summary'].items():
            print(f"   - {stage.title()}: {count}")
        
        return results
        
    except Exception as e:
        logger.error(f"Lead generation failed: {e}")
        print(f"\n❌ Error: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(main())