"""
Industry Classifier

Classifies businesses into industries using NAICS codes, keyword matching,
and business description analysis.
"""

import re
import logging
from typing import Dict, Any, List, Tuple

logger = logging.getLogger(__name__)

class IndustryClassifier:
    """Classifier for business industry categorization."""
    
    def __init__(self):
        """Initialize industry classifier with NAICS mapping."""
        self.naics_mapping = self._build_naics_mapping()
        self.keyword_patterns = self._build_keyword_patterns()
    
    def classify(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify business into industry categories.
        
        Args:
            business_data: Business data dictionary
            
        Returns:
            Enhanced data with industry classification
        """
        classification = {}
        
        try:
            business_name = business_data.get('business_name', '')
            description = business_data.get('business_description', '')
            existing_industry = business_data.get('industry', '')
            
            # Combine text for analysis
            combined_text = f"{business_name} {description} {existing_industry}".lower()
            
            # Attempt classification
            primary_industry, naics_code, confidence = self._classify_by_keywords(combined_text)
            
            classification.update({
                'industry_primary': primary_industry,
                'naics_code': naics_code,
                'industry_confidence': confidence,
                'industry_category': self._get_industry_category(primary_industry),
                'classification_method': 'keyword_matching'
            })
            
            # Add secondary classifications if applicable
            secondary_industries = self._find_secondary_industries(combined_text, primary_industry)
            if secondary_industries:
                classification['industry_secondary'] = ', '.join(secondary_industries)
            
        except Exception as e:
            logger.error(f"Error classifying industry: {e}")
            classification = self._default_classification()
        
        return classification
    
    def _classify_by_keywords(self, text: str) -> Tuple[str, str, int]:
        """
        Classify industry based on keyword matching.
        
        Args:
            text: Combined business text
            
        Returns:
            Tuple of (industry, naics_code, confidence_score)
        """
        best_match = None
        highest_score = 0
        
        for industry, patterns in self.keyword_patterns.items():
            score = 0
            matches = 0
            
            for pattern, weight in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += weight
                    matches += 1
            
            # Normalize score by number of patterns
            if matches > 0:
                normalized_score = score / len(patterns)
                if normalized_score > highest_score:
                    highest_score = normalized_score
                    best_match = industry
        
        if best_match:
            naics_code = self.naics_mapping.get(best_match, {}).get('code', 'UNKNOWN')
            confidence = min(10, int(highest_score * 10))
            return best_match, naics_code, confidence
        else:
            return 'Unknown', 'UNKNOWN', 1
    
    def _find_secondary_industries(self, text: str, primary: str) -> List[str]:
        """Find secondary industry classifications."""
        secondary = []
        
        for industry, patterns in self.keyword_patterns.items():
            if industry == primary:
                continue
                
            score = 0
            for pattern, weight in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    score += weight
            
            # Include as secondary if decent score
            if score >= 2:
                secondary.append(industry)
        
        return secondary[:3]  # Limit to top 3 secondary industries
    
    def _get_industry_category(self, industry: str) -> str:
        """Get high-level industry category."""
        categories = {
            'Technology': [
                'Software Development', 'Internet Service Provider', 'Computer Services',
                'IT Services', 'Telecommunications', 'Data Processing'
            ],
            'Healthcare': [
                'Medical Practice', 'Healthcare Services', 'Pharmaceutical',
                'Medical Equipment', 'Dental Services'
            ],
            'Financial Services': [
                'Banking', 'Insurance', 'Investment Services', 'Real Estate',
                'Financial Planning', 'Accounting'
            ],
            'Professional Services': [
                'Legal Services', 'Consulting', 'Marketing Services',
                'Engineering Services', 'Architectural Services'
            ],
            'Manufacturing': [
                'Manufacturing', 'Construction', 'Industrial Services',
                'Automotive', 'Aerospace'
            ],
            'Retail/Commerce': [
                'Retail', 'E-commerce', 'Wholesale', 'Food Services',
                'Restaurant', 'Hospitality'
            ],
            'Energy/Utilities': [
                'Utilities', 'Energy Services', 'Oil and Gas',
                'Renewable Energy', 'Environmental Services'
            ]
        }
        
        for category, industries in categories.items():
            if industry in industries:
                return category
        
        return 'Other'
    
    def _build_naics_mapping(self) -> Dict[str, Dict[str, str]]:
        """Build NAICS code mapping."""
        return {
            'Internet Service Provider': {
                'code': '517311',
                'description': 'Wired Telecommunications Carriers'
            },
            'Telecommunications': {
                'code': '517000',
                'description': 'Telecommunications'
            },
            'Software Development': {
                'code': '541511',
                'description': 'Custom Computer Programming Services'
            },
            'IT Services': {
                'code': '541512',
                'description': 'Computer Systems Design Services'
            },
            'Computer Services': {
                'code': '541510',
                'description': 'Computer Systems Design and Related Services'
            },
            'Medical Practice': {
                'code': '621111',
                'description': 'Offices of Physicians (except Mental Health Specialists)'
            },
            'Legal Services': {
                'code': '541110',
                'description': 'Offices of Lawyers'
            },
            'Accounting': {
                'code': '541211',
                'description': 'Offices of Certified Public Accountants'
            },
            'Real Estate': {
                'code': '531210',
                'description': 'Offices of Real Estate Agents and Brokers'
            },
            'Insurance': {
                'code': '524210',
                'description': 'Insurance Agencies and Brokerages'
            },
            'Banking': {
                'code': '522110',
                'description': 'Commercial Banking'
            },
            'Restaurant': {
                'code': '722511',
                'description': 'Full-Service Restaurants'
            },
            'Retail': {
                'code': '441000',
                'description': 'Motor Vehicle and Parts Dealers'
            },
            'Manufacturing': {
                'code': '311000',
                'description': 'Food Manufacturing'
            },
            'Construction': {
                'code': '236100',
                'description': 'Residential Building Construction'
            },
            'Consulting': {
                'code': '541611',
                'description': 'Administrative Management and General Management Consulting Services'
            },
            'Marketing Services': {
                'code': '541810',
                'description': 'Advertising Agencies'
            },
            'Engineering Services': {
                'code': '541330',
                'description': 'Engineering Services'
            }
        }
    
    def _build_keyword_patterns(self) -> Dict[str, List[Tuple[str, int]]]:
        """Build keyword patterns for industry classification."""
        return {
            'Internet Service Provider': [
                (r'\bisp\b', 5),
                (r'internet service', 5),
                (r'broadband', 4),
                (r'fiber optic', 4),
                (r'telecommunications', 3),
                (r'cable internet', 4),
                (r'wireless internet', 4),
                (r'network provider', 3)
            ],
            'Telecommunications': [
                (r'telecommunications?', 5),
                (r'telecom', 4),
                (r'phone service', 3),
                (r'wireless', 3),
                (r'cellular', 3),
                (r'mobile service', 3)
            ],
            'Software Development': [
                (r'software development', 5),
                (r'programming', 4),
                (r'application development', 4),
                (r'web development', 4),
                (r'mobile app', 3),
                (r'custom software', 4)
            ],
            'IT Services': [
                (r'it services', 5),
                (r'information technology', 4),
                (r'computer support', 3),
                (r'network services', 3),
                (r'tech support', 3),
                (r'managed services', 4)
            ],
            'Medical Practice': [
                (r'medical', 4),
                (r'physician', 5),
                (r'doctor', 4),
                (r'clinic', 4),
                (r'healthcare', 3),
                (r'dental', 4),
                (r'dentist', 5)
            ],
            'Legal Services': [
                (r'law firm', 5),
                (r'attorney', 5),
                (r'lawyer', 5),
                (r'legal services', 5),
                (r'paralegal', 3)
            ],
            'Real Estate': [
                (r'real estate', 5),
                (r'realtor', 5),
                (r'property management', 4),
                (r'home sales', 3),
                (r'commercial property', 4)
            ],
            'Restaurant': [
                (r'restaurant', 5),
                (r'food service', 4),
                (r'dining', 3),
                (r'cafe', 4),
                (r'bistro', 4),
                (r'eatery', 4)
            ],
            'Retail': [
                (r'retail', 4),
                (r'store', 3),
                (r'shop', 3),
                (r'sales', 2),
                (r'merchandise', 3)
            ],
            'Manufacturing': [
                (r'manufacturing', 5),
                (r'factory', 4),
                (r'production', 3),
                (r'industrial', 3),
                (r'assembly', 3)
            ],
            'Construction': [
                (r'construction', 5),
                (r'contractor', 4),
                (r'building', 3),
                (r'renovation', 3),
                (r'remodeling', 3)
            ],
            'Consulting': [
                (r'consulting', 5),
                (r'consultant', 4),
                (r'advisory', 3),
                (r'business services', 3)
            ],
            'Accounting': [
                (r'accounting', 5),
                (r'accountant', 5),
                (r'cpa', 5),
                (r'bookkeeping', 4),
                (r'tax preparation', 4)
            ],
            'Insurance': [
                (r'insurance', 5),
                (r'coverage', 3),
                (r'policy', 3),
                (r'claims', 3)
            ]
        }
    
    def _default_classification(self) -> Dict[str, Any]:
        """Return default classification for unknown industries."""
        return {
            'industry_primary': 'Unknown',
            'naics_code': 'UNKNOWN',
            'industry_confidence': 1,
            'industry_category': 'Other',
            'classification_method': 'default'
        } 