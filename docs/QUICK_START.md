# 🚀 CRM Lead Generator - Quick Start Guide

Get up and running with the CRM Lead Generation AI Agent in under 10 minutes!

## ⚡ Super Quick Start (5 minutes)

### 1. Prerequisites Check
```bash
# Check Python version (3.9+ required)
python --version

# Check available memory (8GB+ recommended)
# Windows: wmic computersystem get TotalPhysicalMemory
# macOS/Linux: free -h
```

### 2. One-Command Setup
```bash
# Clone and setup everything automatically
git clone <repository-url>
cd CRM_lead_geneartor
pip install -r requirements.txt
python scripts/setup_ollama.py  # This handles Ollama installation and model downloads
```

### 3. Start Generating Leads
```bash
# Start the web interface
python main_app.py

# Open browser to http://localhost:7860
# Generate leads immediately - no additional setup needed!
```

## 📋 Step-by-Step Setup (10 minutes)

### Step 1: System Requirements
- **Python 3.9+** ✅
- **8GB RAM minimum** (16GB recommended) ✅
- **10GB free disk space** ✅
- **Internet connection** for model downloads ✅

### Step 2: Download and Install
```bash
# 1. Clone the repository
git clone <repository-url>
cd CRM_lead_geneartor

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Verify installation
python -c "from src.agents.crm_lead_agent import CRMLeadGenerationAgent; print('✅ Installation successful')"
```

### Step 3: AI Setup (Automated)
```bash
# Run the automated Ollama setup
python scripts/setup_ollama.py

# This will:
# ✅ Check system requirements
# ✅ Install Ollama (if needed)
# ✅ Download AI models (Llama 3.1, Mistral)
# ✅ Test model performance
# ✅ Create configuration files
```

### Step 4: First Lead Generation
```bash
# Option A: Web Interface (Recommended)
python main_app.py
# Open http://localhost:7860 in your browser

# Option B: Command Line Example
python run_isp_nc.py  # Generates ISP leads for North Carolina
```

## 🎯 Quick Examples

### Example 1: Restaurant Leads in San Francisco
1. Open web interface: `python main_app.py`
2. Navigate to "Generate Leads" tab
3. Enter:
   - **Location**: San Francisco, CA
   - **Search Query**: restaurants
   - **Max Results**: 50
4. Click "Generate Leads"
5. Download CSV when complete

### Example 2: ISP Leads (Command Line)
```bash
# Generate ISP leads for North Carolina
python run_isp_nc.py

# Output: data/outputs/isp_leads_north_carolina_[timestamp].csv
# Contains: 14 ISP companies with full contact information
```

### Example 3: Custom Business Search
```python
import asyncio
from src.agents.crm_lead_agent import CRMLeadGenerationAgent
from src.agents.base_agent import Task, TaskPriority

async def generate_custom_leads():
    agent = CRMLeadGenerationAgent()
    
    task = Task(
        task_type="lead_generation",
        description="Generate dental practice leads",
        parameters={
            'search_query': 'dental practice',
            'location': 'Austin, TX',
            'max_results': 25,
            'sources': ['yellow_pages']
        },
        priority=TaskPriority.HIGH
    )
    
    result = await agent.process(task)
    print(f"Generated {result.data['total_leads']} leads")
    print(f"CSV file: {result.data['csv_file_path']}")

# Run the example
asyncio.run(generate_custom_leads())
```

## 🔧 Configuration Quick Setup

### Development Environment (Default)
```bash
# Fast iteration, verbose logging, smaller datasets
export CRM_ENV=development
python main_app.py
```

### Production Environment
```bash
# High reliability, security, performance optimization
export CRM_ENV=production
python main_app.py
```

### Custom Configuration
```bash
# Copy and modify configuration
cp config/development.yaml config/my_config.yaml
# Edit my_config.yaml with your preferences

# Use custom config
export CRM_CONFIG_FILE=config/my_config.yaml
python main_app.py
```

## 🚨 Troubleshooting Quick Fixes

### Issue: "Ollama not found"
```bash
# Manual Ollama installation
# Windows: Download from https://ollama.ai/download
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
```

### Issue: "Models not downloading"
```bash
# Manual model download
ollama pull llama3.1:8b-instruct-q4_K_M
ollama pull mistral:7b-instruct-q4_K_M

# Verify models
ollama list
```

### Issue: "Import errors"
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python path
python -c "import sys; print(sys.path)"
```

### Issue: "No results found"
- Try broader search terms (e.g., "restaurants" instead of "italian restaurants")
- Check location format (use "City, State" format)
- Verify internet connection
- Check if target websites are accessible

### Issue: "Slow performance"
```bash
# Use development config for faster processing
export CRM_ENV=development

# Reduce result count
# In web interface: Set Max Results to 10-25
# In code: max_results=10
```

## 📊 Quick Performance Tips

### Optimize for Speed
1. **Use Development Config**: `export CRM_ENV=development`
2. **Limit Results**: Start with 10-25 leads
3. **Single Source**: Use only Yellow Pages initially
4. **Local LLM**: Ensure Ollama is running for faster AI processing

### Optimize for Quality
1. **Use Production Config**: `export CRM_ENV=production`
2. **Multiple Sources**: Enable Yellow Pages + Yelp
3. **Higher Thresholds**: Increase quality_threshold in config
4. **Full Validation**: Enable all validation checks

## 🎉 Success Indicators

You'll know everything is working when you see:

✅ **Agent Status**: "CRM Lead Generation Agent initialized successfully"  
✅ **Local LLM**: "Ollama service running on http://localhost:11434"  
✅ **Models Available**: "llama3.1:8b-instruct-q4_K_M, mistral:7b-instruct-q4_K_M"  
✅ **Web Interface**: Gradio interface loads at http://localhost:7860  
✅ **Lead Generation**: CSV files appear in `data/outputs/`  

## 🔄 Next Steps

Once you have the basic system running:

1. **Explore Configuration**: Check `config/README.md` for advanced settings
2. **Try Different Sources**: Enable additional data sources
3. **Custom Industries**: Modify industry classification rules
4. **Scale Up**: Increase max_results for larger datasets
5. **Automate**: Set up scheduled lead generation scripts

## 📞 Need Help?

- **Check Logs**: `logs/crm_agent.log` for detailed error information
- **Run Tests**: `python test_import.py` to verify installation
- **Demo Mode**: `python demo_agent.py` for guided walkthrough
- **Health Check**: Use the "Agent Status" tab in web interface

---

**🎯 Goal**: Generate your first 10 high-quality leads in under 10 minutes!

**💡 Tip**: Start with a simple search like "restaurants" in a major city for best results. 