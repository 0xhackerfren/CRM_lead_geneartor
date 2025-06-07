#!/usr/bin/env python3
"""
Test script for Enhanced CRM Application

Tests the core components to ensure they work correctly.
"""

import asyncio
import logging
from src.scrapers import ISPScraper, YellowPagesScraper
from src.processors import CSVGenerator, DataValidator, IndustryClassifier

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_scrapers():
    """Test scraper initialization."""
    print("Testing scrapers...")
    
    try:
        isp_scraper = ISPScraper()
        yp_scraper = YellowPagesScraper()
        print("✅ Scrapers initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Scraper initialization failed: {e}")
        return False

def test_processors():
    """Test processor initialization."""
    print("Testing processors...")
    
    try:
        csv_gen = CSVGenerator()
        validator = DataValidator()
        classifier = IndustryClassifier()
        print("✅ Processors initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Processor initialization failed: {e}")
        return False

def test_industry_classification():
    """Test industry classification."""
    print("Testing industry classification...")
    
    try:
        classifier = IndustryClassifier()
        
        # Test ISP classification
        test_data = {
            'business_name': 'Spectrum Internet Services',
            'business_description': 'Cable internet and broadband provider',
            'industry': 'telecommunications'
        }
        
        result = classifier.classify(test_data)
        print(f"Classification result: {result}")
        
        if result.get('industry_primary') == 'Internet Service Provider':
            print("✅ Industry classification working correctly")
            return True
        else:
            print("❌ Industry classification not working as expected")
            return False
            
    except Exception as e:
        print(f"❌ Industry classification failed: {e}")
        return False

def test_data_validation():
    """Test data validation."""
    print("Testing data validation...")
    
    try:
        validator = DataValidator()
        
        test_data = {
            'business_name': 'Test Company Inc.',
            'phone_number': '555-123-4567',
            'website': 'www.testcompany.com',
            'ceo_name': 'John Smith',
            'ceo_email': 'john@testcompany.com'
        }
        
        result = validator.validate_and_enhance(test_data)
        print(f"Validation result keys: {list(result.keys())}")
        
        if 'data_quality_score' in result:
            print("✅ Data validation working correctly")
            return True
        else:
            print("❌ Data validation not working as expected")
            return False
            
    except Exception as e:
        print(f"❌ Data validation failed: {e}")
        return False

def test_csv_generation():
    """Test CSV generation."""
    print("Testing CSV generation...")
    
    try:
        csv_gen = CSVGenerator()
        
        test_data = [{
            'business_name': 'Test ISP Company',
            'industry_primary': 'Internet Service Provider',
            'ceo_name': 'Jane Doe',
            'phone_number': '(555) 123-4567',
            'website': 'https://www.testisp.com',
            'data_quality_score': 8
        }]
        
        csv_path = csv_gen.generate_csv(test_data, 'test query', 'test location')
        
        if csv_path:
            print(f"✅ CSV generation working correctly: {csv_path}")
            return True
        else:
            print("❌ CSV generation failed")
            return False
            
    except Exception as e:
        print(f"❌ CSV generation failed: {e}")
        return False

async def test_isp_scraper():
    """Test ISP scraper functionality."""
    print("Testing ISP scraper...")
    
    try:
        isp_scraper = ISPScraper()
        
        # Test with known ISPs (should return some results)
        results = isp_scraper.scrape("internet service provider", "North Carolina")
        
        if results and len(results) > 0:
            print(f"✅ ISP scraper working: found {len(results)} results")
            print(f"Sample result: {results[0].get('business_name', 'Unknown')}")
            return True
        else:
            print("❌ ISP scraper returned no results")
            return False
            
    except Exception as e:
        print(f"❌ ISP scraper failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing Enhanced CRM Application Components\n")
    
    tests = [
        test_scrapers,
        test_processors,
        test_industry_classification,
        test_data_validation,
        test_csv_generation
    ]
    
    async_tests = [
        test_isp_scraper
    ]
    
    passed = 0
    total = len(tests) + len(async_tests)
    
    # Run synchronous tests
    for test in tests:
        if test():
            passed += 1
        print()
    
    # Run async tests
    for test in async_tests:
        try:
            if asyncio.run(test()):
                passed += 1
        except Exception as e:
            print(f"❌ Async test failed: {e}")
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Enhanced CRM application is ready.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main() 