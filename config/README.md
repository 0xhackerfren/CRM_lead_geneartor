# CRM Lead Generator Configuration Guide

This directory contains configuration files for the CRM Lead Generation AI Agent system. The configuration system supports environment-specific settings and hierarchical configuration inheritance.

## Configuration Files

### Base Configuration
- **`config.yaml`** - Main configuration file with default settings for all environments

### Environment-Specific Configurations
- **`development.yaml`** - Development environment settings optimized for fast iteration
- **`production.yaml`** - Production environment settings optimized for reliability and performance
- **`testing.yaml`** - Testing environment settings optimized for automated testing and CI/CD

## Usage

### Environment Selection
Set the `CRM_ENV` environment variable to select the configuration:

```bash
# Development (default)
export CRM_ENV=development

# Production
export CRM_ENV=production

# Testing
export CRM_ENV=testing
```

### Configuration Loading
The system loads configuration in the following order (later values override earlier ones):
1. Base configuration (`config.yaml`)
2. Environment-specific configuration (e.g., `development.yaml`)
3. Environment variables (prefixed with `CRM_`)

### Environment Variables
All configuration values can be overridden using environment variables with the `CRM_` prefix:

```bash
# Override logging level
export CRM_LOGGING_LEVEL=DEBUG

# Override scraping rate limit
export CRM_SCRAPING_RATE_LIMIT=1.5

# Override API keys (recommended for production)
export CRM_FALLBACK_APIS_OPENAI_API_KEY=your_api_key_here
export CRM_FALLBACK_APIS_ANTHROPIC_API_KEY=your_api_key_here
```

## Configuration Sections

### Application Settings (`app`)
Basic application configuration including name, version, and debug settings.

```yaml
app:
  name: "CRM Lead Generator"
  version: "1.0.0"
  debug: false
  log_level: "INFO"
  environment: "production"
```

### AI Agent Configuration (`agents`)
Configuration for AI agents, including framework selection and model settings.

```yaml
agents:
  primary_framework: "smol_agents"  # or "langchain"
  fallback_framework: "langchain"
  
  smol_agents:
    model: "Qwen/Qwen2.5-72B-Instruct"
    planning_interval: 3
    max_iterations: 10
    temperature: 0.1
    max_tokens: 2000
```

### Local LLM Configuration (`local_llm`)
Settings for local LLM integration using Ollama or similar platforms.

```yaml
local_llm:
  enabled: true
  platform: "ollama"
  primary_model: "llama3.1:8b-instruct-q4_K_M"
  backup_model: "mistral:7b-instruct-q4_K_M"
  max_response_time: 5.0
  base_url: "http://localhost:11434"
```

### Web Scraping Configuration (`scraping`)
Rate limiting, timeout, and user agent settings for web scraping.

```yaml
scraping:
  rate_limit: 2.0  # seconds between requests
  max_retries: 3
  timeout: 30
  respect_robots_txt: true
  user_agents:
    - "Mozilla/5.0 ..."
```

### Data Sources Configuration (`data_sources`)
Configuration for different business directory sources.

```yaml
data_sources:
  yellow_pages:
    enabled: true
    base_url: "https://www.yellowpages.com"
    max_results_per_page: 30
    priority: 1
```

### Data Processing Configuration (`processing`)
Settings for data processing, validation, and quality assurance.

```yaml
processing:
  batch_size: 50
  max_workers: 4
  quality_threshold: 0.7
  deduplication:
    enabled: true
    similarity_threshold: 0.85
```

### Output Configuration (`output`)
CSV generation and file output settings.

```yaml
output:
  format: "csv"
  include_metadata: true
  output_directory: "data/outputs"
  filename_template: "leads_{timestamp}_{location}.csv"
  fields:
    - "company_name"
    - "business_address"
    # ... additional fields
```

### Geographic Processing (`geographic`)
Geographic data processing and region definitions.

```yaml
geographic:
  enabled: true
  geocoding_service: "nominatim"
  state_subdivision:
    enabled: true
    large_state_threshold: 1000
  regions:
    west_coast: ["CA", "OR", "WA"]
    # ... additional regions
```

### Caching Configuration (`cache`)
Data caching settings for improved performance.

```yaml
cache:
  enabled: true
  type: "sqlite"
  database_path: "data/cache/crm_cache.db"
  expiry_hours: 24
  max_size_mb: 500
```

### Logging Configuration (`logging`)
Comprehensive logging settings with multiple handlers.

```yaml
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  handlers:
    console:
      enabled: true
      level: "INFO"
    file:
      enabled: true
      filename: "logs/crm_agent.log"
```

### Security Configuration (`security`)
Security settings including encryption and access control.

```yaml
security:
  api_key_rotation_days: 30
  encryption:
    enabled: true
    algorithm: "AES-256-GCM"
  access_control:
    enabled: true
    max_failed_attempts: 5
```

## Environment-Specific Features

### Development Environment
- **Fast iteration**: Reduced rate limits and timeouts
- **Verbose logging**: DEBUG level logging with detailed output
- **Smaller datasets**: Limited results for faster testing
- **Hot reload**: Development tools enabled
- **Cost control**: External APIs disabled by default

### Production Environment
- **High reliability**: Conservative rate limits and extensive retries
- **Performance optimization**: Larger batch sizes and worker pools
- **Security hardening**: Encryption, access control, and audit logging
- **Monitoring**: Full performance and business metrics tracking
- **High availability**: Load balancing and health checks

### Testing Environment
- **Mock services**: External dependencies mocked for isolated testing
- **Fast execution**: Minimal timeouts and reduced processing
- **Test data**: Predefined test datasets and fixtures
- **Coverage**: Code coverage tracking and reporting
- **Cleanup**: Automatic cleanup after test execution

## Best Practices

### Security
1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Enable encryption** in production
4. **Rotate API keys** regularly
5. **Monitor access logs** for suspicious activity

### Performance
1. **Adjust rate limits** based on target site policies
2. **Use caching** to reduce redundant requests
3. **Monitor memory usage** for large datasets
4. **Configure worker pools** based on available resources
5. **Enable compression** for large outputs

### Monitoring
1. **Enable structured logging** in production
2. **Set up alerting** for error rates and performance
3. **Track business metrics** like lead quality
4. **Monitor resource usage** to prevent outages
5. **Regular health checks** for all services

### Development
1. **Use development environment** for local work
2. **Enable debug logging** for troubleshooting
3. **Test with small datasets** first
4. **Mock external services** during development
5. **Version control** configuration changes

## Troubleshooting

### Common Issues

**Configuration not loading:**
- Check file permissions
- Verify YAML syntax
- Ensure CRM_ENV is set correctly

**Rate limiting errors:**
- Increase `scraping.rate_limit` value
- Check target site's robots.txt
- Reduce `scraping.max_retries`

**Memory issues:**
- Reduce `processing.batch_size`
- Lower `processing.max_workers`
- Enable caching to reduce memory usage

**Slow performance:**
- Increase `processing.max_workers`
- Enable caching
- Optimize database queries

### Validation
Use the configuration validation tool to check your settings:

```bash
python -m src.config.validator --config config/development.yaml
```

## Configuration Schema

For a complete schema definition, see `src/config/schema.py`. The schema includes:
- Data types for all configuration values
- Valid ranges and constraints
- Required vs optional settings
- Environment-specific validations

## Migration Guide

When upgrading to new versions, configuration changes may be required:

1. **Backup** your current configuration
2. **Review** the changelog for configuration changes
3. **Update** your environment-specific files
4. **Test** the new configuration in development
5. **Validate** using the configuration validator 