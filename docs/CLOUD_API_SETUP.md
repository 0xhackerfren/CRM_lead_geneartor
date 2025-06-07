# 🚀 Cloud API Integration Setup Guide

## Overview

The CRM Lead Generator now supports **cloud AI API integration** with automatic fallback from local LLM processing. This provides:

- **Cost-effective local processing** with Ollama (primary)
- **Reliable cloud fallback** with OpenAI and Anthropic APIs
- **Seamless switching** between local and cloud processing
- **Easy configuration** through the web interface

## 🎯 Quick Start

### 1. Start the Application
```bash
python main_app.py
```

### 2. Access Configuration
- Open your browser to `http://localhost:7861`
- Click on the **"⚙️ Configuration"** tab

### 3. Add API Keys
- **OpenAI**: Enter your `sk-...` API key
- **Anthropic**: Enter your `sk-ant-...` API key
- Click **"💾 Update"** for each provider

### 4. Test Connections
- Click **"🧪 Test OpenAI"** or **"🧪 Test Anthropic"**
- Verify successful connections

### 5. Generate Leads
- Switch to **"🎯 Lead Generation"** tab
- The system will automatically use the best available AI service

## 🔑 Getting API Keys

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click **"Create new secret key"**
4. Copy the key (starts with `sk-...`)
5. **Pricing**: ~$0.50-2.00 per 1000 API calls

### Anthropic API Key
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign in or create an account
3. Navigate to **"API Keys"**
4. Click **"Create Key"**
5. Copy the key (starts with `sk-ant-...`)
6. **Pricing**: ~$0.25-1.50 per 1000 API calls

## ⚙️ Configuration Options

### Local LLM (Recommended Primary)
- **Enabled by default** for privacy and cost savings
- Uses **Ollama** with Llama 3.1 and Mistral models
- **Free** after initial setup
- **Private** - no data sent to external services

### Cloud APIs (Fallback)
- **OpenAI GPT-4o-mini**: Fast, reliable, cost-effective
- **Anthropic Claude 3 Haiku**: High-quality reasoning
- **Automatic fallback**: Used when local LLM fails
- **Pay-per-use**: Only charged when actually used

## 🔄 How Fallback Works

```
1. 🏠 Try Local LLM (Ollama)
   ├─ ✅ Success → Use local result (FREE)
   └─ ❌ Failed → Continue to step 2

2. ☁️ Try OpenAI API
   ├─ ✅ Success → Use OpenAI result (PAID)
   └─ ❌ Failed → Continue to step 3

3. 🧠 Try Anthropic API
   ├─ ✅ Success → Use Anthropic result (PAID)
   └─ ❌ Failed → Return error
```

## 💰 Cost Optimization

### Recommended Setup
1. **Primary**: Local LLM (Ollama) - **FREE**
2. **Fallback 1**: OpenAI GPT-4o-mini - **~$0.50/1000 calls**
3. **Fallback 2**: Anthropic Claude 3 Haiku - **~$0.25/1000 calls**

### Expected Costs
- **Local processing**: 90-95% of requests (FREE)
- **Cloud fallback**: 5-10% of requests (~$5-20/month for heavy usage)
- **Total cost**: Typically under $10/month for most users

## 🛠️ Advanced Configuration

### Environment Variables
```bash
# Optional: Set API keys via environment variables
export OPENAI_API_KEY="sk-your-openai-key"
export ANTHROPIC_API_KEY="sk-ant-your-anthropic-key"

# Optional: Configure local LLM
export CRM_LOCAL_LLM_ENABLED="true"
export OLLAMA_HOST="http://localhost:11434"
```

### Configuration Files
The system supports multiple configuration methods:
- **Web Interface**: Easiest for most users
- **Environment Variables**: Good for deployment
- **Config Files**: Advanced customization

### Model Selection
- **OpenAI**: `gpt-4o-mini` (default), `gpt-4o`, `gpt-3.5-turbo`
- **Anthropic**: `claude-3-haiku-20240307` (default), `claude-3-sonnet-20240229`
- **Local**: `llama3.1:8b-instruct-q4_K_M` (default), `mistral:7b-instruct-q4_K_M`

## 🔧 Troubleshooting

### Common Issues

#### "OpenAI API key not found"
- Verify key starts with `sk-`
- Check key is entered correctly in Configuration tab
- Ensure key has sufficient credits

#### "Anthropic API is disabled"
- Enter API key in Configuration tab
- Click "Update Anthropic Key"
- Verify key starts with `sk-ant-`

#### "All LLM attempts failed"
- Check local Ollama is running: `ollama list`
- Verify at least one cloud API is configured
- Test connections using the "🧪 Test" buttons

#### High API Costs
- Ensure Local LLM is enabled and working
- Check Ollama service: `ollama serve`
- Monitor usage in Configuration tab

### Health Check
Run the test script to verify everything works:
```bash
python test_config.py
```

## 📊 Monitoring Usage

### Configuration Tab Features
- **Real-time status** of all AI services
- **Connection testing** for each provider
- **Usage statistics** and performance metrics
- **Cost tracking** (coming soon)

### Performance Metrics
- **Local success rate**: Percentage using free local processing
- **Cloud fallback rate**: Percentage requiring paid APIs
- **Average response time**: Speed of AI processing
- **Error rate**: Failed requests

## 🚀 Production Deployment

### Recommended Setup
1. **Local LLM**: Always enabled for cost savings
2. **OpenAI**: Enabled for reliable fallback
3. **Anthropic**: Optional secondary fallback
4. **Monitoring**: Track usage and costs

### Security Best Practices
- Store API keys as environment variables
- Use least-privilege API keys
- Monitor usage regularly
- Set up billing alerts

### Scaling Considerations
- Local LLM handles 90%+ of requests
- Cloud APIs provide unlimited scale
- Costs scale linearly with usage
- No infrastructure management needed

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ Configuration tab shows all services as "Enabled"
- ✅ Test connections return "API connection successful"
- ✅ Lead generation completes without errors
- ✅ Local LLM processes most requests (cost-effective)
- ✅ Cloud APIs provide reliable fallback

## 📞 Support

If you encounter issues:
1. Run `python test_config.py` for diagnostics
2. Check the Configuration tab for service status
3. Review logs in `logs/crm_agent.log`
4. Verify API keys and credits
5. Test individual components

---

**🎯 Goal**: Reliable AI-powered lead generation with cost-effective local processing and cloud fallback for maximum reliability! 