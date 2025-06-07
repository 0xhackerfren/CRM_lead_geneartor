"""
Contact Scraper

Specialized scraper for extracting CEO names, emails, and key personnel information
from company websites, LinkedIn profiles, and other sources.
"""

import re
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)

class ContactScraper(BaseScraper):
    """Specialized scraper for extracting leadership and contact information."""
    
    def __init__(self, rate_limit_delay: float = 3.0):
        """Initialize contact scraper with longer delays for respectful crawling."""
        super().__init__(rate_limit_delay)
        
    def scrape(self, query: str, location: str = None, **kwargs) -> List[Dict[str, Any]]:
        """Not used directly - this scraper enhances existing business data."""
        return []
    
    def extract_leadership_contacts(self, website_url: str, company_name: str) -> Dict[str, Any]:
        """
        Extract leadership contact information from a company website.
        
        Args:
            website_url: Company website URL
            company_name: Company name for context
            
        Returns:
            Dictionary with leadership contact information
        """
        contact_info = {}
        
        if not website_url:
            return contact_info
            
        try:
            # First, try to scrape the main website
            main_page_contacts = self._scrape_website_contacts(website_url)
            contact_info.update(main_page_contacts)
            
            # Try to find an "About Us" or "Team" page
            about_page_contacts = self._scrape_about_page(website_url)
            contact_info.update(about_page_contacts)
            
            # Try to find a "Contact" page
            contact_page_info = self._scrape_contact_page(website_url)
            contact_info.update(contact_page_info)
            
        except Exception as e:
            logger.warning(f"Error extracting contacts from {website_url}: {e}")
        
        return contact_info
    
    def _scrape_website_contacts(self, website_url: str) -> Dict[str, Any]:
        """Scrape contact information from the main website page."""
        contact_info = {}
        
        try:
            response = self._make_request(website_url)
            if not response:
                return contact_info
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for CEO/President information on main page
            ceo_info = self._find_ceo_information(soup)
            contact_info.update(ceo_info)
            
            # Look for general email addresses
            emails = self._extract_email_addresses(soup)
            if emails:
                contact_info['general_email'] = emails[0]
                if len(emails) > 1:
                    contact_info['additional_emails'] = emails[1:]
            
        except Exception as e:
            logger.warning(f"Error scraping main website {website_url}: {e}")
        
        return contact_info
    
    def _scrape_about_page(self, website_url: str) -> Dict[str, Any]:
        """Try to find and scrape an About Us or Team page."""
        contact_info = {}
        
        try:
            response = self._make_request(website_url)
            if not response:
                return contact_info
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find links to about/team pages
            about_links = self._find_about_page_links(soup, website_url)
            
            for about_url in about_links[:3]:  # Limit to first 3 about pages
                try:
                    about_response = self._make_request(about_url)
                    if about_response:
                        about_soup = BeautifulSoup(about_response.text, 'html.parser')
                        
                        # Extract leadership information from about page
                        leadership_info = self._extract_leadership_from_about(about_soup)
                        contact_info.update(leadership_info)
                        
                        if contact_info:  # If we found information, don't scrape more pages
                            break
                            
                except Exception as e:
                    logger.warning(f"Error scraping about page {about_url}: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Error finding about pages for {website_url}: {e}")
        
        return contact_info
    
    def _scrape_contact_page(self, website_url: str) -> Dict[str, Any]:
        """Try to find and scrape a Contact page."""
        contact_info = {}
        
        try:
            response = self._make_request(website_url)
            if not response:
                return contact_info
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find links to contact pages
            contact_links = self._find_contact_page_links(soup, website_url)
            
            for contact_url in contact_links[:2]:  # Limit to first 2 contact pages
                try:
                    contact_response = self._make_request(contact_url)
                    if contact_response:
                        contact_soup = BeautifulSoup(contact_response.text, 'html.parser')
                        
                        # Extract contact information
                        page_contact_info = self._extract_contact_from_page(contact_soup)
                        contact_info.update(page_contact_info)
                        
                except Exception as e:
                    logger.warning(f"Error scraping contact page {contact_url}: {e}")
                    continue
        
        except Exception as e:
            logger.warning(f"Error finding contact pages for {website_url}: {e}")
        
        return contact_info
    
    def _find_ceo_information(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Find CEO/President information from webpage content."""
        ceo_info = {}
        
        # Common patterns for CEO information
        ceo_patterns = [
            r'CEO[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'Chief Executive Officer[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'President[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'Founder[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
        ]
        
        text_content = soup.get_text()
        
        for pattern in ceo_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            if matches:
                ceo_info['ceo_name'] = matches[0]
                break
        
        # Look for CEO email patterns
        if ceo_info.get('ceo_name'):
            ceo_name = ceo_info['ceo_name']
            name_parts = ceo_name.lower().split()
            if len(name_parts) >= 2:
                # Common CEO email patterns
                email_patterns = [
                    f"{name_parts[0]}.{name_parts[1]}@",
                    f"{name_parts[0]}@",
                    f"ceo@",
                    f"president@"
                ]
                
                for pattern in email_patterns:
                    email_matches = re.findall(f'{pattern}[\\w.-]+\\.[a-zA-Z]{{2,}}', text_content, re.IGNORECASE)
                    if email_matches:
                        ceo_info['ceo_email'] = email_matches[0]
                        break
        
        return ceo_info
    
    def _extract_email_addresses(self, soup: BeautifulSoup) -> List[str]:
        """Extract email addresses from webpage content."""
        text_content = soup.get_text()
        
        # Email pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text_content)
        
        # Filter out common non-business emails
        filtered_emails = []
        spam_domains = ['example.com', 'test.com', 'gmail.com', 'yahoo.com', 'hotmail.com']
        
        for email in emails:
            domain = email.split('@')[1].lower()
            if not any(spam_domain in domain for spam_domain in spam_domains):
                filtered_emails.append(email)
        
        return filtered_emails[:5]  # Return first 5 business emails
    
    def _find_about_page_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find links to About Us or Team pages."""
        about_links = []
        
        # Common about page link patterns
        about_patterns = [
            'about', 'team', 'leadership', 'management', 'company',
            'who-we-are', 'our-team', 'meet-the-team', 'staff'
        ]
        
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '').lower()
            link_text = link.get_text().lower()
            
            for pattern in about_patterns:
                if pattern in href or pattern in link_text:
                    full_url = urljoin(base_url, link['href'])
                    if full_url not in about_links:
                        about_links.append(full_url)
                    break
        
        return about_links
    
    def _find_contact_page_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Find links to Contact pages."""
        contact_links = []
        
        # Common contact page link patterns
        contact_patterns = ['contact', 'reach-us', 'get-in-touch']
        
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link.get('href', '').lower()
            link_text = link.get_text().lower()
            
            for pattern in contact_patterns:
                if pattern in href or pattern in link_text:
                    full_url = urljoin(base_url, link['href'])
                    if full_url not in contact_links:
                        contact_links.append(full_url)
                    break
        
        return contact_links
    
    def _extract_leadership_from_about(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract leadership information from about/team pages."""
        leadership_info = {}
        
        text_content = soup.get_text()
        
        # Look for leadership roles
        leadership_patterns = {
            'ceo_name': [r'CEO[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)', r'Chief Executive Officer[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)'],
            'president_name': [r'President[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)'],
            'cfo_name': [r'CFO[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)', r'Chief Financial Officer[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)'],
            'cto_name': [r'CTO[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)', r'Chief Technology Officer[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)'],
            'sales_director': [r'VP Sales[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)', r'Sales Director[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)'],
            'marketing_director': [r'VP Marketing[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)', r'Marketing Director[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)']
        }
        
        for role, patterns in leadership_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    leadership_info[role] = matches[0]
                    break
        
        return leadership_info
    
    def _extract_contact_from_page(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract contact information from contact pages."""
        contact_info = {}
        
        # Look for specific contact emails
        text_content = soup.get_text()
        
        # Common business contact patterns
        contact_patterns = {
            'sales_email': [r'sales@[\w.-]+\.[a-zA-Z]{2,}', r'info@[\w.-]+\.[a-zA-Z]{2,}'],
            'support_email': [r'support@[\w.-]+\.[a-zA-Z]{2,}', r'help@[\w.-]+\.[a-zA-Z]{2,}'],
            'general_email': [r'contact@[\w.-]+\.[a-zA-Z]{2,}', r'hello@[\w.-]+\.[a-zA-Z]{2,}']
        }
        
        for contact_type, patterns in contact_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    contact_info[contact_type] = matches[0]
                    break
        
        return contact_info 