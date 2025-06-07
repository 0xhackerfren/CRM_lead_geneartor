#!/usr/bin/env python3
"""
Test script to debug import issues.
"""

import sys
import traceback

def test_imports():
    """Test various imports to identify issues."""
    
    print("🔍 Testing imports...")
    
    # Test 1: Basic src import
    try:
        import src
        print("✅ src module imported successfully")
    except Exception as e:
        print(f"❌ src import failed: {e}")
        traceback.print_exc()
        return
    
    # Test 2: Config import
    try:
        from src.config.settings import get_config
        print("✅ config.settings imported successfully")
    except Exception as e:
        print(f"❌ config.settings import failed: {e}")
        traceback.print_exc()
        return
    
    # Test 3: Base agent import
    try:
        from src.agents.base_agent import BaseAgent
        print("✅ base_agent imported successfully")
    except Exception as e:
        print(f"❌ base_agent import failed: {e}")
        traceback.print_exc()
        return
    
    # Test 4: Utils import
    try:
        from src.utils.local_llm_client import LocalLLMClient
        print("✅ local_llm_client imported successfully")
    except Exception as e:
        print(f"❌ local_llm_client import failed: {e}")
        traceback.print_exc()
        return
    
    # Test 5: Tools import
    try:
        from src.tools.industry_classifier_tool import IndustryClassifierTool
        print("✅ industry_classifier_tool imported successfully")
    except Exception as e:
        print(f"❌ industry_classifier_tool import failed: {e}")
        traceback.print_exc()
        return
    
    # Test 6: CRM agent import
    try:
        from src.agents.crm_lead_agent import CRMLeadGenerationAgent
        print("✅ CRMLeadGenerationAgent imported successfully")
    except Exception as e:
        print(f"❌ CRMLeadGenerationAgent import failed: {e}")
        traceback.print_exc()
        return
    
    # Test 7: Try to create an agent instance
    try:
        agent = CRMLeadGenerationAgent()
        print("✅ CRMLeadGenerationAgent instance created successfully")
    except Exception as e:
        print(f"❌ CRMLeadGenerationAgent instantiation failed: {e}")
        traceback.print_exc()
        return
    
    print("🎉 All imports successful!")

if __name__ == "__main__":
    test_imports() 