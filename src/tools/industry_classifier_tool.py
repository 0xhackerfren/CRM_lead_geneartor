"""
Industry Classifier Tool for CRM Lead Generation.

This tool provides AI-powered industry classification using NAICS codes,
following the industry classification rule.
"""

import asyncio
import json
import logging
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from smolagents import Tool
    SMOLAGENTS_AVAILABLE = True
except ImportError:
    SMOLAGENTS_AVAILABLE = False
    class Tool:
        pass

try:
    from langchain.tools import Tool as LangChainTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)

# Common NAICS code mappings for quick classification
NAICS_MAPPINGS = {
    # Technology and Software
    "software": "541511",
    "technology": "541511", 
    "tech": "541511",
    "computer": "541511",
    "it services": "541511",
    "web development": "541511",
    "app development": "541511",
    "saas": "541511",
    
    # Healthcare
    "medical": "621111",
    "healthcare": "621111",
    "hospital": "622110",
    "clinic": "621111",
    "doctor": "621111",
    "physician": "621111",
    "dentist": "621210",
    "pharmacy": "446110",
    
    # Retail
    "retail": "441000",
    "store": "441000",
    "shop": "441000",
    "clothing": "448110",
    "grocery": "445110",
    "supermarket": "445110",
    "restaurant": "722511",
    "food service": "722511",
    "cafe": "722513",
    "bar": "722410",
    
    # Professional Services
    "consulting": "541611",
    "law": "541110",
    "legal": "541110",
    "attorney": "541110",
    "accounting": "541211",
    "cpa": "541211",
    "real estate": "531210",
    "insurance": "524210",
    "financial": "522110",
    "bank": "522110",
    
    # Construction and Manufacturing
    "construction": "236220",
    "building": "236220",
    "contractor": "236220",
    "manufacturing": "311000",
    "factory": "311000",
    "automotive": "441110",
    "auto repair": "811111",
    
    # Transportation
    "transportation": "484110",
    "trucking": "484121",
    "logistics": "484110",
    "shipping": "484110",
    "delivery": "492210",
    
    # Education
    "education": "611110",
    "school": "611110",
    "university": "611310",
    "college": "611310",
    "training": "611430",
    
    # Entertainment and Recreation
    "entertainment": "711130",
    "fitness": "713940",
    "gym": "713940",
    "sports": "713940",
    "hotel": "721110",
    "lodging": "721110",
    
    # Agriculture
    "agriculture": "111998",
    "farming": "111998",
    "farm": "111998",
    "landscaping": "561730",
    
    # Energy and Utilities
    "energy": "221112",
    "utilities": "221310",
    "solar": "237130",
    "renewable": "237130",
    
    # Nonprofit
    "nonprofit": "813211",
    "charity": "813211",
    "foundation": "813211"
}

# Industry descriptions for NAICS codes
NAICS_DESCRIPTIONS = {
    "541511": "Custom Computer Programming Services",
    "621111": "Offices of Physicians (except Mental Health Specialists)",
    "622110": "General Medical and Surgical Hospitals",
    "621210": "Offices of Dentists",
    "446110": "Pharmacies and Drug Stores",
    "441000": "Motor Vehicle and Parts Dealers",
    "448110": "Men's Clothing Stores",
    "445110": "Supermarkets and Other Grocery (except Convenience) Stores",
    "722511": "Full-Service Restaurants",
    "722513": "Limited-Service Restaurants",
    "722410": "Drinking Places (Alcoholic Beverages)",
    "541611": "Administrative Management and General Management Consulting Services",
    "541110": "Offices of Lawyers",
    "541211": "Offices of Certified Public Accountants",
    "531210": "Offices of Real Estate Agents and Brokers",
    "524210": "Insurance Agencies and Brokerages",
    "522110": "Commercial Banking",
    "236220": "Commercial and Institutional Building Construction",
    "311000": "Food Manufacturing",
    "441110": "New Car Dealers",
    "811111": "General Automotive Repair",
    "484110": "General Freight Trucking, Local",
    "484121": "General Freight Trucking, Long-Distance, Truckload",
    "492210": "Local Messengers and Local Delivery",
    "611110": "Elementary and Secondary Schools",
    "611310": "Colleges, Universities, and Professional Schools",
    "611430": "Professional and Management Development Training",
    "711130": "Musical Groups and Artists",
    "713940": "Fitness and Recreational Sports Centers",
    "721110": "Hotels (except Casino Hotels) and Motels",
    "111998": "All Other Miscellaneous Crop Farming",
    "561730": "Landscaping Services",
    "221112": "Fossil Fuel Electric Power Generation",
    "221310": "Water Supply and Irrigation Systems",
    "237130": "Power and Communication Line and Related Structures Construction",
    "813211": "Grantmaking Foundations",
    "999999": "Unclassified Establishments"
}

class IndustryClassifierTool:
    """
    Industry classifier tool using AI and keyword matching for business classification.
    
    Combines AI-powered classification with keyword-based fallback for robust
    industry identification using NAICS codes.
    """
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
        self.logger = logging.getLogger("tools.industry_classifier")
        
        # Performance tracking
        self.stats = {
            'total_classifications': 0,
            'ai_classifications': 0,
            'keyword_classifications': 0,
            'failed_classifications': 0,
            'average_confidence': 0.0
        }
        
        self.logger.info("Industry classifier tool initialized")
    
    async def classify(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a business's industry using AI and keyword matching.
        
        Args:
            business_info: Dictionary containing business information
            
        Returns:
            Classification result with NAICS code and confidence
        """
        self.stats['total_classifications'] += 1
        
        try:
            # First, try AI classification if LLM client available
            if self.llm_client:
                ai_result = await self._classify_with_ai(business_info)
                
                if ai_result['success'] and ai_result['confidence_score'] > 70:
                    self.stats['ai_classifications'] += 1
                    self._update_average_confidence(ai_result['confidence_score'])
                    
                    self.logger.info(
                        f"AI classification successful: {ai_result['naics_code']} "
                        f"(confidence: {ai_result['confidence_score']})"
                    )
                    
                    return ai_result
            
            # Fallback to keyword-based classification
            keyword_result = self._classify_with_keywords(business_info)
            self.stats['keyword_classifications'] += 1
            self._update_average_confidence(keyword_result['confidence_score'])
            
            self.logger.info(
                f"Keyword classification: {keyword_result['naics_code']} "
                f"(confidence: {keyword_result['confidence_score']})"
            )
            
            return keyword_result
            
        except Exception as e:
            self.stats['failed_classifications'] += 1
            error_msg = f"Classification failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            
            return {
                'success': False,
                'naics_code': '999999',
                'industry_description': 'Classification failed',
                'confidence_score': 0,
                'reasoning': error_msg,
                'source': 'error',
                'model': 'none'
            }
    
    async def _classify_with_ai(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """Classify using AI/LLM."""
        try:
            result = await self.llm_client.classify_industry(business_info)
            
            # Validate NAICS code format
            naics_code = result.get('naics_code', '000000')
            if not re.match(r'^\d{6}$', naics_code):
                # Try to extract valid NAICS code
                naics_match = re.search(r'\b\d{6}\b', str(naics_code))
                if naics_match:
                    naics_code = naics_match.group()
                else:
                    naics_code = '999999'
            
            # Get description from our database if available
            industry_description = result.get('industry_description', 'Unknown')
            if naics_code in NAICS_DESCRIPTIONS:
                industry_description = NAICS_DESCRIPTIONS[naics_code]
            
            return {
                'success': result.get('success', False),
                'naics_code': naics_code,
                'industry_description': industry_description,
                'confidence_score': min(result.get('confidence_score', 0), 100),
                'reasoning': result.get('reasoning', ''),
                'source': result.get('source', 'ai'),
                'model': result.get('model', 'unknown')
            }
            
        except Exception as e:
            self.logger.warning(f"AI classification failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _classify_with_keywords(self, business_info: Dict[str, Any]) -> Dict[str, Any]:
        """Classify using keyword matching as fallback."""
        try:
            # Extract text for keyword matching
            text_fields = [
                business_info.get('company_name', ''),
                business_info.get('business_description', ''),
                business_info.get('industry', ''),
                business_info.get('category', ''),
                business_info.get('website_content', '')
            ]
            
            combined_text = ' '.join(text_fields).lower()
            
            # Score keywords based on matches
            keyword_scores = {}
            
            for keyword, naics_code in NAICS_MAPPINGS.items():
                score = 0
                
                # Exact keyword match
                if keyword in combined_text:
                    score += 10
                
                # Partial matches
                keyword_words = keyword.split()
                for word in keyword_words:
                    if word in combined_text:
                        score += 3
                
                if score > 0:
                    keyword_scores[naics_code] = keyword_scores.get(naics_code, 0) + score
            
            # Find best match
            if keyword_scores:
                best_naics = max(keyword_scores, key=keyword_scores.get)
                confidence = min(keyword_scores[best_naics] * 5, 85)  # Cap at 85% for keyword matching
                
                return {
                    'success': True,
                    'naics_code': best_naics,
                    'industry_description': NAICS_DESCRIPTIONS.get(best_naics, 'Unknown Industry'),
                    'confidence_score': confidence,
                    'reasoning': f'Keyword-based classification (score: {keyword_scores[best_naics]})',
                    'source': 'keyword',
                    'model': 'keyword_matching'
                }
            
            # No good match found
            return {
                'success': True,
                'naics_code': '999999',
                'industry_description': 'Unclassified Establishments',
                'confidence_score': 20,
                'reasoning': 'No clear industry indicators found',
                'source': 'keyword',
                'model': 'keyword_matching'
            }
            
        except Exception as e:
            self.logger.error(f"Keyword classification failed: {e}")
            
            return {
                'success': False,
                'naics_code': '999999',
                'industry_description': 'Classification error',
                'confidence_score': 0,
                'reasoning': f'Keyword classification error: {str(e)}',
                'source': 'error',
                'model': 'keyword_matching'
            }
    
    def _update_average_confidence(self, confidence: float):
        """Update running average confidence score."""
        total_class = self.stats['total_classifications']
        current_avg = self.stats['average_confidence']
        
        self.stats['average_confidence'] = (
            (current_avg * (total_class - 1) + confidence) / total_class
        )
    
    def get_naics_info(self, naics_code: str) -> Dict[str, Any]:
        """
        Get information about a NAICS code.
        
        Args:
            naics_code: 6-digit NAICS code
            
        Returns:
            Information about the NAICS code
        """
        return {
            'naics_code': naics_code,
            'description': NAICS_DESCRIPTIONS.get(naics_code, 'Unknown'),
            'is_valid': naics_code in NAICS_DESCRIPTIONS
        }
    
    def search_naics_by_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search for NAICS codes by keyword.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of matching NAICS codes and descriptions
        """
        keyword = keyword.lower()
        matches = []
        
        # Search in keyword mappings
        for kw, naics_code in NAICS_MAPPINGS.items():
            if keyword in kw or kw in keyword:
                matches.append({
                    'naics_code': naics_code,
                    'description': NAICS_DESCRIPTIONS.get(naics_code, 'Unknown'),
                    'keyword_match': kw,
                    'relevance': 'exact' if keyword == kw else 'partial'
                })
        
        # Search in descriptions
        for naics_code, description in NAICS_DESCRIPTIONS.items():
            if keyword in description.lower():
                if not any(m['naics_code'] == naics_code for m in matches):
                    matches.append({
                        'naics_code': naics_code,
                        'description': description,
                        'keyword_match': keyword,
                        'relevance': 'description'
                    })
        
        return matches
    
    def get_stats(self) -> Dict[str, Any]:
        """Get classification statistics."""
        total = self.stats['total_classifications']
        
        return {
            'total_classifications': total,
            'ai_success_rate': (self.stats['ai_classifications'] / total * 100) if total > 0 else 0,
            'keyword_fallback_rate': (self.stats['keyword_classifications'] / total * 100) if total > 0 else 0,
            'failure_rate': (self.stats['failed_classifications'] / total * 100) if total > 0 else 0,
            'average_confidence': round(self.stats['average_confidence'], 2),
            'supported_keywords': len(NAICS_MAPPINGS),
            'naics_database_size': len(NAICS_DESCRIPTIONS)
        }
    
    def to_smol_tool(self):
        """Convert to SmolAgents tool format."""
        if not SMOLAGENTS_AVAILABLE:
            return None
        
        class IndustryClassifierSmolTool(Tool):
            name = "industry_classifier"
            description = """
            Classify businesses into industries using NAICS codes.
            Use this tool when you need to determine the industry classification
            of a business based on company name, description, or other business information.
            """
            inputs = {
                "business_info": {
                    "type": "object",
                    "description": "Dictionary with business information including company_name, business_description, etc."
                }
            }
            output_type = "object"
            
            def __init__(self, classifier_tool):
                super().__init__()
                self.classifier = classifier_tool
            
            async def forward(self, business_info):
                result = await self.classifier.classify(business_info)
                return {
                    "naics_code": result['naics_code'],
                    "industry_description": result['industry_description'],
                    "confidence_score": result['confidence_score'],
                    "classification_source": result.get('source', 'unknown')
                }
        
        return IndustryClassifierSmolTool(self)
    
    def to_langchain_tool(self):
        """Convert to LangChain tool format."""
        if not LANGCHAIN_AVAILABLE:
            return None
        
        async def classify_industry(business_info: str) -> str:
            """Classify a business industry based on business information."""
            try:
                # Parse input if it's a string
                if isinstance(business_info, str):
                    import json
                    try:
                        business_data = json.loads(business_info)
                    except json.JSONDecodeError:
                        # Treat as company name
                        business_data = {"company_name": business_info}
                else:
                    business_data = business_info
                
                result = await self.classify(business_data)
                
                return f"NAICS Code: {result['naics_code']}, Industry: {result['industry_description']}, Confidence: {result['confidence_score']}%"
                
            except Exception as e:
                return f"Classification failed: {str(e)}"
        
        return LangChainTool(
            name="industry_classifier",
            description="Classify businesses into industries using NAICS codes",
            func=classify_industry
        ) 