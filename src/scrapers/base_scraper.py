"""
Base Scraper Class

Abstract base class for all web scrapers in the CRM lead generation system.
Provides common functionality for rate limiting, session management, and error handling.
"""

import requests
import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Abstract base class for all web scrapers."""
    
    def __init__(self, rate_limit_delay: float = 2.0):
        """
        Initialize base scraper.
        
        Args:
            rate_limit_delay: Delay between requests in seconds
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.rate_limit_delay = rate_limit_delay
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Implement rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Make a rate-limited HTTP request.
        
        Args:
            url: URL to request
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object or None if failed
        """
        try:
            self._rate_limit()
            response = self.session.get(url, timeout=30, **kwargs)
            
            if response.status_code == 200:
                return response
            else:
                logger.warning(f"Request failed with status {response.status_code}: {url}")
                return None
                
        except Exception as e:
            logger.error(f"Request error for {url}: {e}")
            return None
    
    @abstractmethod
    def scrape(self, query: str, location: str = None, **kwargs) -> List[Dict[str, Any]]:
        """
        Abstract method for scraping data.
        
        Args:
            query: Search query
            location: Geographic location filter
            **kwargs: Additional scraper-specific parameters
            
        Returns:
            List of business data dictionaries
        """
        pass
    
    def _extract_contact_info(self, soup, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract enhanced contact information including CEO and key personnel.
        
        Args:
            soup: BeautifulSoup object of business page
            business_data: Existing business data dictionary
            
        Returns:
            Enhanced business data with contact information
        """
        # This will be implemented by specific scrapers
        return business_data
    
    def _validate_business_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate that business data contains required fields.
        
        Args:
            data: Business data dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ['business_name']
        return all(field in data and data[field] for field in required_fields)
    
    def _standardize_phone(self, phone: str) -> str:
        """
        Standardize phone number format.
        
        Args:
            phone: Raw phone number string
            
        Returns:
            Standardized phone number
        """
        if not phone:
            return ""
        
        # Remove all non-digit characters
        digits = ''.join(filter(str.isdigit, phone))
        
        # Format as (XXX) XXX-XXXX if 10 digits
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == '1':
            return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone  # Return original if can't standardize
    
    def _clean_website_url(self, url: str) -> str:
        """
        Clean and standardize website URL.
        
        Args:
            url: Raw URL string
            
        Returns:
            Cleaned URL with https:// prefix
        """
        if not url:
            return ""
        
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url 