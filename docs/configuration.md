# Configuration Guide

This guide explains how to configure the Dental Insurance Guidelines Web Scraper for your specific needs.

## Configuration Files

The scraper uses two main configuration files:

1. `.env` - Environment variables and sensitive information
2. `config.yaml` - General scraper configuration

## Environment Variables (`.env`)

The `.env` file stores sensitive information and environment-specific settings. Never commit this file to version control.

```ini
# Provider Portal Credentials
AETNA_USERNAME=your_username
AETNA_PASSWORD=your_password
CIGNA_USERNAME=your_username
CIGNA_PASSWORD=your_password
METLIFE_USERNAME=your_username
METLIFE_PASSWORD=your_password
UHC_USERNAME=your_username
UHC_PASSWORD=your_password

# Proxy Configuration
USE_PROXY=true
PROXY_ROTATION_INTERVAL=60
PROXY_URL=http://localhost:8118

# Output Configuration
OUTPUT_DIR=./data
PDF_STORAGE_DIR=./pdfs
LOG_LEVEL=INFO

# Database Configuration (optional)
DB_HOST=localhost
DB_PORT=27017
DB_NAME=insurance_data
```

## Scraper Configuration (`config.yaml`)

The `config.yaml` file controls the scraper's behavior and settings.

```yaml
scraper:
  # General Settings
  rate_limit: 5  # requests per second
  max_retries: 3
  retry_delay: 60  # seconds
  timeout: 30  # seconds
  
  # Output Settings
  output_format: json  # json or csv
  compress_output: true
  save_pdfs: true
  
  # Proxy Settings
  proxy:
    enabled: true
    rotate_every: 60  # seconds
    max_failures: 3
    
  # Logging
  logging:
    level: INFO
    file: scraper.log
    format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Carrier-specific Settings
carriers:
  aetna:
    enabled: true
    base_url: "https://www.aetna.com/health-care-professionals"
    login_url: "https://www.aetna.com/health-care-professionals/login.html"
    rate_limit: 3  # carrier-specific rate limit
    pdf_enabled: true
    
  cigna:
    enabled: true
    base_url: "https://www.cigna.com/healthcare-providers"
    login_url: "https://www.cigna.com/healthcare-providers/login"
    rate_limit: 5
    pdf_enabled: true
    
  metlife:
    enabled: true
    base_url: "https://www.metlife.com/dental-providers"
    login_url: "https://www.metlife.com/dental-providers/login"
    rate_limit: 4
    pdf_enabled: true
    
  uhc:
    enabled: true
    base_url: "https://www.uhc.com/dental-providers"
    login_url: "https://www.uhc.com/dental-providers/login"
    rate_limit: 3
    pdf_enabled: true

# PDF Processing Settings
pdf:
  max_size: 50000000  # 50MB
  timeout: 300  # seconds
  ocr_enabled: true
  ocr_language: eng
  
  extraction:
    use_tables: true
    extract_images: false
    merge_lines: true
    
  validation:
    check_corruption: true
    verify_text: true
    min_text_length: 100

# Error Handling
errors:
  max_failures: 5
  alert_on_failure: true
  alert_email: "admin@example.com"
  
  retry_on:
    - ConnectionError
    - TimeoutError
    - HTTPError
    
  ignore:
    - ResourceWarning
```

## Configuration Schema

The configuration is validated using Pydantic models. Here's the schema definition:

```python
from pydantic import BaseModel, HttpUrl, EmailStr
from typing import List, Optional, Dict

class ProxyConfig(BaseModel):
    enabled: bool
    rotate_every: int
    max_failures: int

class LoggingConfig(BaseModel):
    level: str
    file: str
    format: str

class CarrierConfig(BaseModel):
    enabled: bool
    base_url: HttpUrl
    login_url: HttpUrl
    rate_limit: int
    pdf_enabled: bool

class PDFConfig(BaseModel):
    max_size: int
    timeout: int
    ocr_enabled: bool
    ocr_language: str
    extraction: Dict
    validation: Dict

class ErrorConfig(BaseModel):
    max_failures: int
    alert_on_failure: bool
    alert_email: EmailStr
    retry_on: List[str]
    ignore: List[str]

class ScraperConfig(BaseModel):
    rate_limit: int
    max_retries: int
    retry_delay: int
    timeout: int
    output_format: str
    compress_output: bool
    save_pdfs: bool
    proxy: ProxyConfig
    logging: LoggingConfig
    carriers: Dict[str, CarrierConfig]
    pdf: PDFConfig
    errors: ErrorConfig
```

## Environment-Specific Configuration

You can maintain different configurations for different environments:

```
config/
  ├── config.yaml          # Default configuration
  ├── config.dev.yaml      # Development settings
  ├── config.test.yaml     # Testing settings
  └── config.prod.yaml     # Production settings
```

Load environment-specific config:

```bash
python -m scraper run --config config/config.prod.yaml
```

## Configuration Best Practices

1. **Security**
   - Never commit `.env` files to version control
   - Use environment variables for sensitive data
   - Rotate credentials regularly
   - Use secure connections (HTTPS)

2. **Performance**
   - Adjust rate limits based on carrier requirements
   - Configure appropriate timeouts
   - Enable caching when possible
   - Monitor resource usage

3. **Maintenance**
   - Document all configuration changes
   - Use version control for config files
   - Maintain changelog for config updates
   - Regular config review and cleanup

4. **Error Handling**
   - Configure appropriate retry policies
   - Set up alerts for critical failures
   - Log configuration issues
   - Validate config before running

## Troubleshooting

If you encounter configuration issues:

1. Validate your configuration:
   ```bash
   python -m scraper validate-config
   ```

2. Check the logs for configuration-related errors:
   ```bash
   tail -f scraper.log | grep CONFIG
   ```

3. Test your configuration:
   ```bash
   python -m scraper test-config
   ```

## Support

For configuration-related issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review carrier-specific documentation
3. Contact support team 