# Installation Guide

This guide will help you set up the Dental Insurance Guidelines Web Scraper on your system.

## System Requirements

- Python 3.11 or higher
- pip (Python package installer)
- Git
- Docker (optional, for containerized deployment)
- 2GB RAM minimum (4GB recommended)
- 10GB free disk space

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/insurance-web-scraper.git
cd insurance-web-scraper
```

### 2. Set Up Python Environment

We recommend using a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

### 4. Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your credentials:
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

   # Proxy Configuration (optional)
   USE_PROXY=true
   PROXY_ROTATION_INTERVAL=60

   # Output Configuration
   OUTPUT_DIR=./data
   PDF_STORAGE_DIR=./pdfs
   ```

### 5. Docker Installation (Optional)

If you prefer using Docker:

1. Build the image:
   ```bash
   docker build -t insurance-scraper .
   ```

2. Run the container:
   ```bash
   docker run -v $(pwd)/data:/app/data \
             -v $(pwd)/pdfs:/app/pdfs \
             -v $(pwd)/.env:/app/.env \
             insurance-scraper
   ```

## Verification

To verify your installation:

1. Run the test suite:
   ```bash
   pytest
   ```

2. Try a sample extraction:
   ```bash
   python -m scraper test
   ```

## Common Issues

### SSL Certificate Errors

If you encounter SSL certificate errors:

1. Update your CA certificates:
   ```bash
   pip install --upgrade certifi
   ```

2. Set the SSL certificate path:
   ```bash
   export SSL_CERT_FILE=/path/to/cacert.pem
   ```

### Proxy Configuration

If you're behind a corporate proxy:

1. Set HTTP/HTTPS proxy environment variables:
   ```bash
   export HTTP_PROXY="http://proxy.company.com:8080"
   export HTTPS_PROXY="http://proxy.company.com:8080"
   ```

2. Update your `.env` file with proxy settings:
   ```ini
   CORPORATE_PROXY=http://proxy.company.com:8080
   ```

## Next Steps

- Review the [Configuration Guide](configuration.md) to customize the scraper
- Check the [Usage Examples](usage.md) for common scenarios
- Set up monitoring and alerts as needed

## Support

If you encounter any issues during installation:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Search existing [GitHub Issues](https://github.com/yourusername/insurance-scraper/issues)
3. Create a new issue if needed 