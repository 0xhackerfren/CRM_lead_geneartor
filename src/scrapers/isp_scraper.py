"""
ISP Scraper

Specialized web scraper for Internet Service Providers (ISPs).
Includes enhanced contact information extraction for CEO names, emails, and key personnel.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
from .contact_scraper import ContactScraper

logger = logging.getLogger(__name__)

class ISPScraper(BaseScraper):
    """Specialized scraper for Internet Service Providers."""
    
    def __init__(self, rate_limit_delay: float = 2.0):
        """Initialize ISP scraper with contact extraction capabilities."""
        super().__init__(rate_limit_delay)
        self.contact_scraper = ContactScraper(rate_limit_delay)
        
    def scrape(self, query: str, location: str = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Scrape ISP data from multiple sources.
        
        Args:
            query: Search query (should contain ISP-related terms)
            location: Geographic location to search
            **kwargs: Additional parameters
            
        Returns:
            List of ISP business data with enhanced contact information
        """
        all_results = []
        
        # Scrape from Yellow Pages
        yp_results = self._scrape_yellow_pages_isp(location)
        all_results.extend(yp_results)
        
        # Add known major ISPs for the location
        major_isps = self._get_major_isps_for_location(location)
        all_results.extend(major_isps)
        
        # Enhance contact information for all results
        enhanced_results = []
        for business in all_results:
            enhanced_business = self._enhance_contact_information(business)
            enhanced_results.append(enhanced_business)
        
        return self._deduplicate_businesses(enhanced_results)
    
    def _scrape_yellow_pages_isp(self, location: str) -> List[Dict[str, Any]]:
        """Scrape ISP listings from Yellow Pages."""
        logger.info(f"Scraping Yellow Pages for ISPs in {location}")
        results = []
        
        if not location:
            return results
            
        try:
            # Yellow Pages search URL for ISPs
            search_url = f"https://www.yellowpages.com/search?search_terms=internet+service+provider&geo_location_terms={location.replace(' ', '+')}"
            
            response = self._make_request(search_url)
            if not response:
                return results
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find business listings
            listings = soup.find_all('div', class_='result')
            
            for listing in listings[:20]:  # Limit to first 20 results
                try:
                    business_data = self._extract_yp_business_data(listing)
                    if business_data and self._is_isp_business(business_data):
                        business_data['source'] = 'yellow_pages'
                        business_data['industry'] = 'Internet Service Provider'
                        business_data['naics_code'] = '517311'
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
            if not name_elem:
                name_elem = listing.find('h3', class_='n')
            business_name = name_elem.get_text(strip=True) if name_elem else ''
            
            # Extract address
            address_elem = listing.find('p', class_='adr') or listing.find('span', class_='adr')
            address = address_elem.get_text(strip=True) if address_elem else ''
            
            # Extract phone
            phone_elem = listing.find('div', class_='phones') or listing.find('span', class_='phone')
            phone = phone_elem.get_text(strip=True) if phone_elem else ''
            phone = self._standardize_phone(phone)
            
            # Extract website
            website_elem = listing.find('a', class_='track-visit-website')
            website = website_elem.get('href', '') if website_elem else ''
            website = self._clean_website_url(website)
            
            # Extract description
            desc_elem = listing.find('p', class_='snippet') or listing.find('div', class_='snippet')
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            if business_name:
                return {
                    'business_name': business_name,
                    'address': address,
                    'phone_number': phone,
                    'website': website,
                    'business_description': description,
                    'data_quality_score': self._calculate_data_quality_score({
                        'business_name': business_name,
                        'address': address,
                        'phone_number': phone,
                        'website': website,
                        'business_description': description
                    })
                }
        except Exception as e:
            logger.warning(f"Error extracting business data: {e}")
        
        return None
    
    def _is_isp_business(self, business_data: Dict[str, Any]) -> bool:
        """Check if business data represents an ISP."""
        isp_keywords = [
            'internet', 'isp', 'broadband', 'fiber', 'cable', 'wireless',
            'telecommunications', 'telecom', 'network', 'connectivity'
        ]
        
        name = business_data.get('business_name', '').lower()
        description = business_data.get('business_description', '').lower()
        
        return any(keyword in name or keyword in description for keyword in isp_keywords)
    
    def _get_major_isps_for_location(self, location: str) -> List[Dict[str, Any]]:
        """Get known major ISPs for a specific location."""
        if not location:
            return []
            
        state = location.upper()
        
        # Major national ISPs available in most states
        national_isps = [
            {
                'business_name': 'Spectrum (Charter Communications)',
                'address': f'Multiple locations across {location}',
                'phone_number': '(855) 243-8892',
                'website': 'https://www.spectrum.com',
                'business_description': f'Cable internet, TV, and phone services throughout {location}',
                'service_type': 'Cable',
                'coverage': 'Statewide',
                'source': 'known_provider',
                'industry': 'Internet Service Provider',
                'naics_code': '517311'
            },
            {
                'business_name': 'AT&T Internet',
                'address': f'Multiple locations across {location}',
                'phone_number': '(800) 288-2020',
                'website': 'https://www.att.com',
                'business_description': f'DSL, fiber, and wireless internet services in {location}',
                'service_type': 'DSL/Fiber',
                'coverage': 'Statewide',
                'source': 'known_provider',
                'industry': 'Internet Service Provider',
                'naics_code': '517311'
            },
            {
                'business_name': 'Verizon',
                'address': f'Multiple locations across {location}',
                'phone_number': '(800) 837-4966',
                'website': 'https://www.verizon.com',
                'business_description': f'Fiber and wireless internet services in {location}',
                'service_type': 'Fiber/Wireless',
                'coverage': 'Select areas',
                'source': 'known_provider',
                'industry': 'Internet Service Provider',
                'naics_code': '517311'
            },
            {
                'business_name': 'CenturyLink (Lumen)',
                'address': f'Multiple locations across {location}',
                'phone_number': '(866) 642-0444',
                'website': 'https://www.centurylink.com',
                'business_description': f'DSL and fiber internet services across {location}',
                'service_type': 'DSL/Fiber',
                'coverage': 'Statewide',
                'source': 'known_provider',
                'industry': 'Internet Service Provider',
                'naics_code': '517311'
            }
        ]
        
        # Add state-specific ISPs
        if 'NORTH CAROLINA' in state or 'NC' in state:
            state_specific = [
                {
                    'business_name': 'Wilkes Communications',
                    'address': 'North Wilkesboro, NC',
                    'phone_number': '(336) 838-7000',
                    'website': 'https://www.wilkes.net',
                    'business_description': 'Local fiber and cable internet provider serving northwest North Carolina',
                    'service_type': 'Fiber/Cable',
                    'coverage': 'Northwest NC',
                    'source': 'known_provider',
                    'industry': 'Internet Service Provider',
                    'naics_code': '517311'
                },
                {
                    'business_name': 'SkyLine/SkyBest',
                    'address': 'West Jefferson, NC',
                    'phone_number': '(800) 759-2226',
                    'website': 'https://www.skybest.com',
                    'business_description': 'Local telecommunications and internet provider serving western North Carolina',
                    'service_type': 'Fiber/DSL',
                    'coverage': 'Western NC',
                    'source': 'known_provider',
                    'industry': 'Internet Service Provider',
                    'naics_code': '517311'
                }
            ]
            national_isps.extend(state_specific)
        
        # Add data quality scores
        for isp in national_isps:
            isp['data_quality_score'] = self._calculate_data_quality_score(isp)
            
        return national_isps
    
    def _enhance_contact_information(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance business data with CEO and key personnel contact information.
        
        Args:
            business_data: Basic business information
            
        Returns:
            Enhanced business data with contact information
        """
        enhanced_data = business_data.copy()
        
        # Use the contact scraper to find CEO and key personnel
        if business_data.get('website'):
            contact_info = self.contact_scraper.extract_leadership_contacts(
                business_data['website'], 
                business_data['business_name']
            )
            enhanced_data.update(contact_info)
        
        # Set default values for missing contact fields
        contact_fields = [
            'ceo_name', 'ceo_email', 'ceo_linkedin',
            'president_name', 'cfo_name', 'cto_name',
            'sales_director', 'marketing_director'
        ]
        
        for field in contact_fields:
            if field not in enhanced_data:
                enhanced_data[field] = 'NOT_FOUND'
        
        return enhanced_data
    
    def _calculate_data_quality_score(self, data: Dict[str, Any]) -> int:
        """
        Calculate data quality score (1-10) based on completeness and accuracy.
        
        Args:
            data: Business data dictionary
            
        Returns:
            Quality score from 1 to 10
        """
        score = 0
        max_score = 10
        
        # Business name (required) - 2 points
        if data.get('business_name'):
            score += 2
        
        # Contact information - 3 points total
        if data.get('phone_number'):
            score += 1
        if data.get('website'):
            score += 1
        if data.get('address'):
            score += 1
        
        # Description - 1 point
        if data.get('business_description'):
            score += 1
        
        # Enhanced contact info - 3 points total
        if data.get('ceo_name') and data.get('ceo_name') != 'NOT_FOUND':
            score += 1
        if data.get('ceo_email') and data.get('ceo_email') != 'NOT_FOUND':
            score += 1
        if data.get('service_type'):
            score += 1
        
        # Industry classification - 1 point
        if data.get('industry') or data.get('naics_code'):
            score += 1
        
        return min(score, max_score)
    
    def _deduplicate_businesses(self, businesses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate businesses based on name similarity."""
        if not businesses:
            return []
        
        unique_businesses = []
        seen_names = set()
        
        for business in businesses:
            name = business.get('business_name', '').lower().strip()
            
            # Simple deduplication based on name similarity
            name_normalized = re.sub(r'[^\w\s]', '', name)
            name_words = set(name_normalized.split())
            
            is_duplicate = False
            for seen_name in seen_names:
                seen_words = set(seen_name.split())
                # Check if names have significant overlap
                overlap = len(name_words.intersection(seen_words))
                if overlap >= 2 and (overlap / len(name_words) > 0.6 or overlap / len(seen_words) > 0.6):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_businesses.append(business)
                seen_names.add(name_normalized)
        
        return unique_businesses 