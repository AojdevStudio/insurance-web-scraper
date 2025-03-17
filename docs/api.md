# API Documentation

This document describes the programmatic interface for the Dental Insurance Guidelines Web Scraper.

## Core Classes

### Scraper

The main scraper class that handles the extraction process.

```python
from scraper import Scraper

# Initialize scraper
scraper = Scraper(
    config_path="config.yaml",
    credentials_path=".env"
)

# Run scraper
results = scraper.run(
    carriers=["aetna", "cigna"],
    validate=True
)
```

#### Constructor Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| config_path | str | Yes | Path to configuration file |
| credentials_path | str | Yes | Path to credentials file |
| log_level | str | No | Logging level (DEBUG, INFO, etc.) |
| proxy | str | No | Proxy URL |
| timeout | int | No | Request timeout in seconds |

#### Methods

##### run()

Runs the scraper for specified carriers.

```python
def run(
    carriers: List[str] = None,
    validate: bool = True,
    incremental: bool = False,
    since: str = None,
    output_dir: str = "./data",
    format: str = "json"
) -> Dict[str, Any]
```

##### process_pdfs()

Processes downloaded PDF files.

```python
def process_pdfs(
    input_dir: str,
    output_dir: str,
    pattern: str = None
) -> List[Dict[str, Any]]
```

##### validate_data()

Validates extracted data against schema.

```python
def validate_data(
    data: Dict[str, Any],
    schema_path: str = None
) -> bool
```

### CarrierBase

Base class for carrier-specific implementations.

```python
from scraper.carriers import CarrierBase

class CustomCarrier(CarrierBase):
    def login(self):
        # Implementation
        pass

    def get_guidelines(self):
        # Implementation
        pass

    def extract_data(self):
        # Implementation
        pass
```

#### Required Methods

| Method | Description |
|--------|-------------|
| login() | Handles carrier authentication |
| get_guidelines() | Retrieves guidelines documents |
| extract_data() | Extracts structured data |

## Data Models

### GuidelineData

Represents extracted guideline data.

```python
from scraper.models import GuidelineData

guideline = GuidelineData(
    procedure_code="D0150",
    description="Comprehensive oral evaluation",
    requirements=["New patient", "Once per 36 months"],
    documentation=["Chart notes", "X-rays if applicable"],
    frequency="36 months",
    age_restrictions=None
)
```

#### Properties

| Property | Type | Description |
|----------|------|-------------|
| procedure_code | str | CDT procedure code |
| description | str | Procedure description |
| requirements | List[str] | List of requirements |
| documentation | List[str] | Required documentation |
| frequency | str | Frequency limitations |
| age_restrictions | Dict | Age-related restrictions |

### ExtractionRule

Defines data extraction patterns.

```python
from scraper.models import ExtractionRule

rule = ExtractionRule(
    pattern=r"D\d{4}",
    flags=re.IGNORECASE,
    required=True,
    multiline=False
)
```

## Configuration

### YAML Configuration

Example configuration structure:

```yaml
scraper:
  rate_limit: 60
  timeout: 30
  retries: 3
  
carriers:
  aetna:
    base_url: "https://example.com"
    login_path: "/login"
    guidelines_path: "/guidelines"
    
extraction_rules:
  procedure_code:
    pattern: "D\\d{4}"
    required: true
  requirements:
    pattern: "Requirements:.*?(?=\\n\\n)"
    multiline: true
```

### Environment Variables

Required environment variables:

```bash
# Carrier Credentials
AETNA_USERNAME=user
AETNA_PASSWORD=pass

# Proxy Configuration
PROXY_URL=http://proxy:8080
PROXY_USERNAME=user
PROXY_PASSWORD=pass

# Output Configuration
OUTPUT_DIR=./data
OUTPUT_FORMAT=json

# Optional Settings
DEBUG=true
LOG_LEVEL=INFO
```

## Events and Callbacks

### Event Handlers

Register callbacks for scraper events:

```python
from scraper.events import ScraperEvents

def on_guideline_extracted(data):
    print(f"Extracted: {data['procedure_code']}")

scraper = Scraper()
scraper.events.on(ScraperEvents.GUIDELINE_EXTRACTED, on_guideline_extracted)
```

Available events:

| Event | Description |
|-------|-------------|
| SCRAPER_STARTED | Scraper initialization |
| LOGIN_SUCCESS | Successful carrier login |
| PDF_DOWNLOADED | PDF file downloaded |
| GUIDELINE_EXTRACTED | Data extracted |
| VALIDATION_ERROR | Data validation error |
| SCRAPER_COMPLETED | Scraper completion |

## Error Handling

### Exception Classes

```python
from scraper.exceptions import (
    ScraperError,
    AuthenticationError,
    ExtractionError,
    ValidationError
)

try:
    scraper.run()
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except ExtractionError as e:
    print(f"Extraction failed: {e}")
except ValidationError as e:
    print(f"Validation failed: {e}")
except ScraperError as e:
    print(f"General error: {e}")
```

### Error Types

| Exception | Description |
|-----------|-------------|
| ScraperError | Base exception class |
| AuthenticationError | Login/authentication failure |
| ExtractionError | Data extraction failure |
| ValidationError | Data validation failure |
| NetworkError | Network/connection issues |
| PDFError | PDF processing errors |

## Utilities

### Helper Functions

```python
from scraper.utils import (
    validate_procedure_code,
    parse_frequency,
    clean_text,
    download_file
)

# Validate CDT code
is_valid = validate_procedure_code("D0150")

# Parse frequency string
months = parse_frequency("once per 36 months")

# Clean extracted text
clean = clean_text("Some  messy\n\ntext")

# Download file
success = download_file("https://example.com/file.pdf", "./downloads")
```

### Constants

```python
from scraper.constants import (
    CARRIERS,
    PROCEDURE_CODE_PATTERN,
    DEFAULT_TIMEOUT,
    MAX_RETRIES
)
```

## Testing

### Unit Tests

```python
from scraper.testing import ScraperTestCase

class TestCustomCarrier(ScraperTestCase):
    def setUp(self):
        self.scraper = Scraper(
            config_path="tests/config.yaml",
            credentials_path="tests/.env"
        )
    
    def test_login(self):
        success = self.scraper.login()
        self.assertTrue(success)
    
    def test_extraction(self):
        data = self.scraper.extract_data()
        self.assertIsNotNone(data)
```

### Mock Data

```python
from scraper.testing import MockCarrier

# Use mock carrier for testing
mock_carrier = MockCarrier()
mock_carrier.add_guideline(
    procedure_code="D0150",
    requirements=["Test requirement"]
)
```

## Performance Optimization

### Caching

```python
from scraper.cache import Cache

# Initialize cache
cache = Cache(expire_after=3600)

# Cache data
cache.set("key", "value")

# Get cached data
value = cache.get("key")
```

### Batch Processing

```python
from scraper.batch import BatchProcessor

# Process in batches
processor = BatchProcessor(batch_size=100)
processor.add_items(items)
results = processor.process()
```

## Integration

### Database Integration

```python
from scraper.storage import DatabaseStorage

# Initialize storage
storage = DatabaseStorage(
    connection_string="postgresql://user:pass@localhost/db"
)

# Store results
storage.save_guidelines(results)
```

### Export Formats

```python
from scraper.export import (
    CSVExporter,
    JSONExporter,
    ExcelExporter
)

# Export to CSV
exporter = CSVExporter()
exporter.export(data, "output.csv")

# Export to JSON
exporter = JSONExporter()
exporter.export(data, "output.json")

# Export to Excel
exporter = ExcelExporter()
exporter.export(data, "output.xlsx")
```

## Best Practices

1. **Error Handling**
   - Always catch specific exceptions
   - Implement proper logging
   - Use retry mechanisms

2. **Performance**
   - Implement caching
   - Use batch processing
   - Monitor memory usage

3. **Security**
   - Use environment variables
   - Implement rate limiting
   - Validate input data

4. **Maintenance**
   - Keep dependencies updated
   - Monitor carrier changes
   - Regular testing 