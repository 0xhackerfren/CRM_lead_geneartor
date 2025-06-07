"""
Directory Scrapers

Scrapers for business directories like Yellow Pages, Google Business, and other
online business databases with enhanced web crawling capabilities.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
from .base_scraper import BaseScraper
from .contact_scraper import ContactScraper

logger = logging.getLogger(__name__)

class YellowPagesScraper(BaseScraper):
    """Enhanced Yellow Pages scraper with deep web crawling."""
    
    def __init__(self, rate_limit_delay: float = 2.5):
        """Initialize with contact enhancement capabilities."""
        super().__init__(rate_limit_delay)
        self.contact_scraper = ContactScraper(rate_limit_delay + 1.0)
        
    def scrape(self, query: str, location: str = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Scrape businesses from Yellow Pages with enhanced contact extraction.
        
        Args:
            query: Business search query
            location: Geographic location
            **kwargs: Additional parameters like max_results
            
        Returns:
            List of enhanced business data
        """
        max_results = kwargs.get('max_results', 50)
        results = []
        
        try:
            # Build search URL
            search_url = self._build_search_url(query, location)
            logger.info(f"Searching Yellow Pages: {search_url}")
            
            # Scrape multiple pages if needed
            page = 1
            while len(results) < max_results and page <= 5:  # Limit to 5 pages
                page_results = self._scrape_page(search_url, page)
                if not page_results:
                    break
                    
                # Enhance each result with contact information
                for business in page_results:
                    enhanced_business = self._enhance_business_data(business)
                    results.append(enhanced_business)
                    
                    if len(results) >= max_results:
                        break
                
                page += 1
                
        except Exception as e:
            logger.error(f"Error scraping Yellow Pages: {e}")
        
        return results[:max_results]
    
    def _build_search_url(self, query: str, location: str) -> str:
        """Build Yellow Pages search URL."""
        base_url = "https://www.yellowpages.com/search"
        
        # Encode search terms
        search_terms = quote_plus(query)
        geo_location = quote_plus(location) if location else ""
        
        if geo_location:
            return f"{base_url}?search_terms={search_terms}&geo_location_terms={geo_location}"
        else:
            return f"{base_url}?search_terms={search_terms}"
    
    def _scrape_page(self, base_url: str, page: int) -> List[Dict[str, Any]]:
        """Scrape a single page of results."""
        results = []
        
        try:
            # Add page parameter
            if page > 1:
                url = f"{base_url}&page={page}"
            else:
                url = base_url
                
            response = self._make_request(url)
            if not response:
                return results
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find business listings - try multiple selectors
            listings = (
                soup.find_all('div', class_='result') or
                soup.find_all('div', class_='search-results organic') or
                soup.find_all('article', class_='result')
            )
            
            logger.info(f"Found {len(listings)} listings on page {page}")
            
            for listing in listings:
                business_data = self._extract_business_data(listing)
                if business_data:
                    business_data['source'] = 'yellow_pages'
                    business_data['page_scraped'] = page
                    results.append(business_data)
                    
        except Exception as e:
            logger.error(f"Error scraping page {page}: {e}")
        
        return results
    
    def _extract_business_data(self, listing) -> Optional[Dict[str, Any]]:
        """Extract comprehensive business data from a listing."""
        try:
            business_data = {}
            
            # Business name - try multiple selectors
            name_elem = (
                listing.find('a', class_='business-name') or
                listing.find('h3', class_='n') or
                listing.find('h2', class_='n') or
                listing.find('span', class_='business-name')
            )
            
            if not name_elem:
                return None
                
            business_data['business_name'] = name_elem.get_text(strip=True)
            
            # Address
            address_elem = (
                listing.find('p', class_='adr') or
                listing.find('span', class_='adr') or
                listing.find('div', class_='adr')
            )
            business_data['address'] = address_elem.get_text(strip=True) if address_elem else ''
            
            # Phone number
            phone_elem = (
                listing.find('div', class_='phones') or
                listing.find('span', class_='phone') or
                listing.find('a', class_='phone')
            )
            phone = phone_elem.get_text(strip=True) if phone_elem else ''
            business_data['phone_number'] = self._standardize_phone(phone)
            
            # Website
            website_elem = (
                listing.find('a', class_='track-visit-website') or
                listing.find('a', {'data-track': 'visit-website'}) or
                listing.find('a', class_='website')
            )
            website = website_elem.get('href', '') if website_elem else ''
            business_data['website'] = self._clean_website_url(website)
            
            # Business description
            desc_elem = (
                listing.find('p', class_='snippet') or
                listing.find('div', class_='snippet') or
                listing.find('span', class_='categories')
            )
            business_data['business_description'] = desc_elem.get_text(strip=True) if desc_elem else ''
            
            # Extract additional details if available
            business_data.update(self._extract_additional_details(listing))
            
            # Calculate initial data quality score
            business_data['data_quality_score'] = self._calculate_quality_score(business_data)
            
            return business_data
            
        except Exception as e:
            logger.warning(f"Error extracting business data: {e}")
            return None
    
    def _extract_additional_details(self, listing) -> Dict[str, Any]:
        """Extract additional business details from listing."""
        details = {}
        
        try:
            # Business hours
            hours_elem = listing.find('div', class_='hours') or listing.find('span', class_='hours')
            if hours_elem:
                details['business_hours'] = hours_elem.get_text(strip=True)
            
            # Business categories/industry
            category_elem = (
                listing.find('div', class_='categories') or
                listing.find('span', class_='categories') or
                listing.find('p', class_='categories')
            )
            if category_elem:
                details['industry'] = category_elem.get_text(strip=True)
            
            # Rating if available
            rating_elem = listing.find('div', class_='ratings') or listing.find('span', class_='rating')
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    details['rating'] = float(rating_match.group(1))
            
            # Number of reviews
            review_elem = listing.find('span', class_='count') or listing.find('div', class_='review-count')
            if review_elem:
                review_text = review_elem.get_text(strip=True)
                review_match = re.search(r'(\d+)', review_text)
                if review_match:
                    details['review_count'] = int(review_match.group(1))
                    
        except Exception as e:
            logger.warning(f"Error extracting additional details: {e}")
        
        return details
    
    def _enhance_business_data(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance business data with deep web crawling for contact information.
        """
        enhanced_data = business_data.copy()
        
        # If we have a website, crawl it for enhanced contact information
        if business_data.get('website'):
            try:
                logger.info(f"Enhancing contact info for {business_data['business_name']}")
                contact_info = self.contact_scraper.extract_leadership_contacts(
                    business_data['website'],
                    business_data['business_name']
                )
                enhanced_data.update(contact_info)
                
                # Update quality score after enhancement
                enhanced_data['data_quality_score'] = self._calculate_quality_score(enhanced_data)
                
            except Exception as e:
                logger.warning(f"Error enhancing contact info for {business_data['business_name']}: {e}")
        
        # Set default values for missing contact fields
        contact_fields = [
            'ceo_name', 'ceo_email', 'ceo_linkedin',
            'president_name', 'cfo_name', 'cto_name',
            'sales_director', 'marketing_director',
            'general_email', 'sales_email'
        ]
        
        for field in contact_fields:
            if field not in enhanced_data:
                enhanced_data[field] = 'NOT_FOUND'
        
        return enhanced_data
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> int:
        """Calculate data quality score (1-10)."""
        score = 0
        
        # Required fields
        if data.get('business_name'):
            score += 2
        
        # Basic contact info
        if data.get('phone_number'):
            score += 1
        if data.get('address'):
            score += 1
        if data.get('website'):
            score += 1
        
        # Enhanced contact info
        if data.get('ceo_name') and data.get('ceo_name') != 'NOT_FOUND':
            score += 2
        if data.get('ceo_email') and data.get('ceo_email') != 'NOT_FOUND':
            score += 1
        
        # Additional business info
        if data.get('business_description'):
            score += 1
        if data.get('industry'):
            score += 1
        
        return min(score, 10)


class GoogleBusinessScraper(BaseScraper):
    """Scraper for Google Business listings (future implementation)."""
    
    def scrape(self, query: str, location: str = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Scrape Google Business listings.
        
        Note: This requires special handling due to Google's anti-bot measures.
        For now, returns empty list - can be implemented with proper API access.
        """
        logger.info("Google Business scraping not yet implemented - requires API access")
        return [] 