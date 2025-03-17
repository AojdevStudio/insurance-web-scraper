# Scrapy settings for dental_scraper project

BOT_NAME = 'dental_scraper'

SPIDER_MODULES = ['dental_scraper.spiders']
NEWSPIDER_MODULE = 'dental_scraper.spiders'

# Disable robots.txt completely
ROBOTSTXT_OBEY = False
ROBOTSTXT_ENABLED = False

# Configure maximum concurrent requests performing at the same time to the same domain
CONCURRENT_REQUESTS = 1

# Configure a delay for requests for the same website
DOWNLOAD_DELAY = 3

# Enable cookies
COOKIES_ENABLED = True

# Override the default request headers
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Configure retry settings
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403]

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': 90,
    'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
}

# Configure logging
LOG_LEVEL = 'INFO'
LOG_FORMAT = '%(asctime)s [%(name)s] %(levelname)s: %(message)s'

# Configure output directory
OUTPUT_DIR = 'data/processed'
PDF_DIR = 'data/pdfs'

# Configure timeout
DOWNLOAD_TIMEOUT = 30

# Allow all HTTP status codes
HTTPERROR_ALLOW_ALL = True 