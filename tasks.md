# Dental Insurance Guidelines Web Scraper - Task Breakdown

## Sprint 1: Setup & Initial Development (Day 1)

### Environment Setup
- [x] **Story 1.1: Docker Environment Configuration**
  - Set up Dockerfile with Python 3.11
  - Configure development environment with required dependencies
  - Create docker-compose.yml for local development
  - Document environment setup process
  - AC: Docker environment builds and runs successfully

  <IMPORTANT_NOTES>
  1. Network Configuration:
     - Use bridge network with custom DNS (8.8.8.8, 8.8.4.4)
     - Consider host network mode for strict IP validation
     - Implement proper network isolation between services

  2. Proxy Setup:
     - Include rotating-proxy service (mattes/rotating-proxy:latest)
     - Configure 5 TOR instances with 60-second circuit rotation
     - Set up proxy environment variables for scraper service
     - Implement user-agent rotation alongside IP rotation

  3. Volume Configuration:
     - PDF storage: ./pdfs:/app/pdfs
     - Extracted data: ./extracted_data:/app/data
     - Cache storage: ./cache:/app/cache
     - Ensure proper permissions and ownership

  4. Resource Limits:
     - Memory: 2GB limit for PDF processing
     - CPU: 2 cores allocation
     - Implement restart policy: unless-stopped
     - Monitor resource usage during testing

  5. Multi-Container Architecture:
     - Scraper service (Python 3.11)
     - MongoDB for structured data
     - Qdrant for vector database
     - Ensure service communication via shared network

  Example docker-compose.yml structure provided in documentation.
  </IMPORTANT_NOTES>

- [x] **Story 1.2: Python Dependencies Setup**
  - Create requirements.txt with specific versions
  - Install and configure Scrapy
  - Install and configure PyPDF2/pdfplumber
  - Set up logging configuration
  - AC: All dependencies install without conflicts

  <IMPORTANT_NOTES>
  1. Core Dependencies (requirements.txt):
     ```
     # Web Scraping
     Scrapy==2.11.0
     beautifulsoup4==4.12.3
     lxml==5.1.0
     selenium==4.18.1  # For JavaScript-heavy sites
     fake-useragent==1.4.0  # For user agent rotation

     # PDF Processing
     pdfplumber==0.10.3
     PyPDF2==3.0.1

     # Database
     pymongo==4.6.1
     qdrant-client==1.7.0
     motor==3.3.2  # Async MongoDB driver

     # Utilities
     python-dotenv==1.0.1
     loguru==0.7.2
     tenacity==8.2.3  # For retry logic
     aiohttp==3.9.3  # Async HTTP client
     ```

  2. Development Dependencies:
     ```
     # Testing
     pytest==8.0.2
     pytest-asyncio==0.23.5
     pytest-cov==4.1.0
     pytest-mock==3.12.0

     # Code Quality
     black==24.2.0
     flake8==7.0.0
     mypy==1.8.0
     isort==5.13.2

     # Documentation
     Sphinx==7.2.6
     sphinx-rtd-theme==2.0.0
     ```

  3. Dependency Management:
     - Use pip-compile to generate requirements.txt
     - Separate prod and dev requirements
     - Pin all versions for reproducibility
     - Document any custom package modifications

  4. Configuration Priorities:
     - Scrapy: Configure concurrent requests and delays
     - PDF Tools: Set memory limits for large files
     - Logging: Use loguru with structured output
     - Database: Configure connection pooling

  5. Security Considerations:
     - Regular dependency updates for security
     - Vulnerability scanning with safety
     - Audit package permissions
     - Use environment variables for sensitive configs
  </IMPORTANT_NOTES>

### Base Architecture
- [x] **Story 1.3: Base Scraper Architecture**
  - Create base Spider class with common functionality
  - Implement rate limiting middleware
  - Set up error handling framework
  - Create logging utilities
  - AC: Base spider successfully handles requests and responses

  <IMPORTANT_NOTES>
  1. Base Spider Class Structure:
     ```python
     class InsuranceSpider(scrapy.Spider):
         # Required Configuration
         name = None  # Set by carrier-specific spiders
         allowed_domains = []  # Set by carrier-specific spiders
         custom_settings = {
             'CONCURRENT_REQUESTS': 1,  # Default conservative setting
             'DOWNLOAD_DELAY': 5,  # Default 5-second delay
             'COOKIES_ENABLED': True,
             'ROBOTSTXT_OBEY': True,
         }

         # Common Fields
         carrier_name = None
         base_url = None
         login_required = False
         pdf_enabled = False
         javascript_required = False
     ```

  2. Rate Limiting Configuration:
     - Base delay: 5 seconds between requests
     - Carrier-specific delays in spider settings:
       ```python
       CARRIER_DELAYS = {
           'aetna': 7,
           'cigna': 5,
           'metlife': 6,
           'uhc': 8
       }
       ```
     - Implement exponential backoff for 429 responses
     - Track request counts per domain/endpoint

  3. Error Handling Framework:
     - Network Errors:
       * Connection timeouts (30s default)
       * DNS failures
       * SSL/TLS errors
       * Proxy failures
     - HTTP Errors:
       * 403: Rotate IP/user agent
       * 429: Implement backoff
       * 500-599: Retry with exponential backoff
     - Parsing Errors:
       * Missing elements
       * Changed structure
       * Invalid PDF format
     - Authentication Errors:
       * Session expiration
       * Invalid credentials
       * CAPTCHA detection

  4. Retry Logic:
     ```python
     RETRY_SETTINGS = {
         'max_retries': 3,
         'retry_statuses': [500, 502, 503, 504, 429],
         'retry_delay': {
             'initial': 60,  # seconds
             'multiplier': 2,
             'max_delay': 300  # 5 minutes
         }
     }
     ```

  5. Logging Configuration:
     - Use loguru with structured output
     - Log levels:
       * DEBUG: Request/response details
       * INFO: Successful extractions
       * WARNING: Retries/recoverable errors
       * ERROR: Failed extractions
       * CRITICAL: System failures
     - Include metadata:
       * Carrier name
       * URL
       * Timestamp
       * Request ID
       * IP address used
     - Store logs in ./logs/carrier_name/YYYY-MM-DD.log

  6. Authentication Handling:
     - Support multiple auth methods:
       * Basic auth
       * Form-based login
       * Token-based auth
       * Cookie-based sessions
     - Implement session management
     - Handle login form detection
     - Store credentials securely

  7. Download Handlers:
     - PDF handler for direct downloads
     - HTML-to-PDF conversion
     - File size limits (50MB default)
     - Checksum verification
     - Duplicate detection

  8. Middleware Stack:
     ```python
     SPIDER_MIDDLEWARES = {
         'scrapy.spidermiddlewares.httperror.HttpErrorMiddleware': 100,
         'project.middlewares.RateLimitMiddleware': 200,
         'project.middlewares.ProxyRotationMiddleware': 300,
         'project.middlewares.UserAgentMiddleware': 400,
         'project.middlewares.RetryMiddleware': 500,
         'project.middlewares.AuthenticationMiddleware': 600,
     }
     ```
  </IMPORTANT_NOTES>

- [x] **Story 1.4: Data Model Implementation**
  - Create data models for carrier information
  - Implement procedure code structure
  - Set up JSON output formatting
  - Create data validation utilities
  - AC: Data model matches specified JSON structure

  <IMPORTANT_NOTES>
  1. Core Data Models (using Pydantic):
     ```python
     from pydantic import BaseModel, Field, HttpUrl, validator
     from typing import List, Optional
     from datetime import date
     
     class Procedure(BaseModel):
         code: str = Field(..., pattern=r'^D\d{4}$')
         description: str
         requirements: List[str]
         notes: Optional[str] = None
         
         @validator('code')
         def validate_cdt_code(cls, v):
             if not v.startswith('D') or not len(v) == 5:
                 raise ValueError('Invalid CDT code format')
             return v

     class CarrierGuidelines(BaseModel):
         carrier: str
         year: int = Field(..., ge=2024, le=2026)
         source_url: HttpUrl
         last_updated: date
         procedures: List[Procedure]
         metadata: dict = Field(default_factory=dict)
     ```

  2. Validation Rules:
     - CDT Codes:
       * Must start with 'D'
       * Must be followed by 4 digits
       * Must be valid 2024-2025 codes
     - Dates:
       * ISO format (YYYY-MM-DD)
       * Year range validation (2024-2026)
     - URLs:
       * Must be valid HTTPS URLs
       * Must match carrier domains
     - Requirements:
       * Non-empty list
       * No duplicate entries
       * Standardized formatting

  3. Data Transformations:
     ```python
     class DataTransformer:
         def standardize_requirements(self, reqs: List[str]) -> List[str]:
             # Remove duplicates
             # Normalize whitespace
             # Standardize common terms
             # Sort by importance
             pass

         def normalize_cdt_code(self, code: str) -> str:
             # Ensure uppercase D
             # Add leading zeros if needed
             # Validate against CDT code list
             pass

         def clean_description(self, desc: str) -> str:
             # Remove special characters
             # Standardize terminology
             # Fix common typos
             pass
     ```

  4. Carrier-Specific Adaptors:
     ```python
     class CarrierAdaptor(BaseModel):
         # Custom fields per carrier
         custom_fields: dict = Field(default_factory=dict)
         
         def to_standard_format(self) -> CarrierGuidelines:
             # Convert carrier-specific format to standard
             pass
         
         def from_standard_format(self, data: CarrierGuidelines):
             # Convert standard format to carrier-specific
             pass
     ```

  5. Output Formats:
     - JSON (default):
       * Pretty printed for readability
       * UTF-8 encoded
       * Sorted keys for consistency
     - CSV Export:
       * Flattened procedure structure
       * One row per procedure/requirement
       * Headers matching standard terms
     - Vector DB Format:
       * Procedure text embedding
       * Requirement text embedding
       * Metadata preservation

  6. Data Quality Checks:
     ```python
     class DataValidator:
         def validate_completeness(self, data: CarrierGuidelines) -> bool:
             # Check required fields
             # Verify procedure codes exist
             # Validate requirements present
             pass

         def validate_consistency(self, data: CarrierGuidelines) -> bool:
             # Check terminology consistency
             # Verify requirement formats
             # Validate against known patterns
             pass

         def generate_quality_report(self, data: CarrierGuidelines) -> dict:
             # Missing data summary
             # Format issues
             # Consistency scores
             pass
     ```

  7. Storage Integration:
     - MongoDB Schema:
       * Indexed fields for quick lookup
       * Versioning support
       * Audit trail
     - Vector DB Integration:
       * Embedding generation
       * Similarity search support
       * Metadata preservation
  </IMPORTANT_NOTES>

### Initial Carrier Implementation
- [x] **Story 1.5: First Carrier Spider (Aetna)**
  - Research Aetna's provider portal structure
  - Implement carrier-specific spider
  - Create HTML parsing functions
  - Test basic data extraction
  - AC: Successfully extracts guidelines from Aetna

  <IMPORTANT_NOTES>
  1. Spider Configuration:
     ```python
     class AetnaSpider(InsuranceSpider):
         name = 'aetna'
         allowed_domains = ['aetna.com']
         carrier_name = 'Aetna'
         base_url = 'https://www.aetna.com/health-care-professionals/resources.html'
         pdf_enabled = True  # Primary source is PDF
         
         custom_settings = {
             'CONCURRENT_REQUESTS': 2,  # Can be more aggressive since no rate limiting
             'DOWNLOAD_DELAY': 2,
             'ROBOTSTXT_OBEY': True,
             'DOWNLOAD_TIMEOUT': 60,  # Extended for PDF downloads
         }
     ```

  2. PDF Download Strategy:
     - Target Location: resources section
     - File Pattern: Look for "2025" and "guidelines" in PDF names
     - Storage: ./pdfs/aetna/YYYY/filename.pdf
     - Checksum tracking to avoid redownloading
     - Implement PDF validation before processing

  3. PDF Processing Pipeline:
     ```python
     class AetnaPDFProcessor:
         def extract_guidelines(self, pdf_path: str) -> List[Procedure]:
             # Extract text from PDF
             # Identify procedure code sections
             # Parse requirements and notes
             # Apply Aetna-specific formatting rules
             pass

         def parse_procedure_section(self, text: str) -> Procedure:
             # Extract CDT code
             # Parse description
             # Identify documentation requirements
             # Extract special notes
             pass
     ```

  4. Data Extraction Rules:
     - CDT Code Pattern: Look for "D" followed by 4 digits
     - Requirements: Usually bullet-pointed lists
     - Notes: Often in separate sections or boxes
     - Tables: Extract using pdfplumber table detection

  5. Quality Checks:
     - Verify PDF is 2025 version
     - Validate all extracted CDT codes
     - Ensure requirements list is not empty
     - Check for common Aetna-specific terms
     - Compare against 2024 data for major changes

  6. Implementation Steps:
     1. Start with resources page navigation
     2. Identify and download relevant PDFs
     3. Extract text content from PDFs
     4. Parse procedure codes and requirements
     5. Transform to standard data model
     6. Validate extracted data
     7. Store in MongoDB and vector DB

  7. Testing Strategy:
     - Mock PDF downloads in tests
     - Use sample PDF sections for parsing tests
     - Validate against known Aetna formats
     - Compare output against sample data
     - Test error handling with corrupt PDFs

  8. Success Criteria:
     - All 2025 procedure codes extracted
     - Requirements properly associated with codes
     - No missing mandatory fields
     - Data matches Aetna's formatting
     - Successful export to standard format
  </IMPORTANT_NOTES>

## Sprint 2: Main Development (Day 1-2)

### PDF Processing
- [x] **Story 2.1: PDF Extraction Setup**
  - Implement PDF text extraction
  - Create table parsing utilities
  - Set up pattern matching for procedure codes
  - Implement PDF download handling
  - AC: Successfully extracts text and tables from sample PDFs

  <IMPORTANT_NOTES>
  1. PDF Text Extraction Engine:
     ```python
     class PDFExtractor:
         def __init__(self):
             self.pdf_handler = pdfplumber.open
             self.backup_handler = PyPDF2.PdfReader
             self.max_file_size = 50 * 1024 * 1024  # 50MB limit

         async def extract_text(self, pdf_path: str) -> str:
             # Try pdfplumber first, fallback to PyPDF2
             # Handle OCR if needed
             # Clean and normalize extracted text
             pass

         async def extract_tables(self, pdf_path: str) -> List[Dict]:
             # Use pdfplumber's table detection
             # Convert tables to structured data
             # Handle merged cells and spanning
             pass
     ```

  2. Table Parsing Configuration:
     ```python
     TABLE_SETTINGS = {
         'vertical_strategy': 'text',
         'horizontal_strategy': 'lines',
         'intersection_x_tolerance': 3,
         'intersection_y_tolerance': 3,
         'snap_x_tolerance': 3,
         'snap_y_tolerance': 3,
         'edge_min_length': 3,
         'min_words_vertical': 3,
         'min_words_horizontal': 1
     }
     ```

  3. Pattern Matching Rules:
     - CDT Code Patterns:
       ```python
       PATTERNS = {
           'cdt_code': r'D\d{4}',
           'procedure_header': r'^(?:Procedure|CDT Code|Service):?\s*([D]\d{4})',
           'requirements_section': r'(?:Requirements|Documentation Required|Necessary Information):',
           'notes_section': r'(?:Notes|Special Considerations|Additional Information):'
       }
       ```

  4. Download Handler:
     ```python
     class PDFDownloadHandler:
         async def download(self, url: str, filename: str) -> str:
             # Verify URL is PDF
             # Check file size before download
             # Stream download with progress
             # Verify PDF integrity
             # Store with proper naming
             pass

         def validate_pdf(self, path: str) -> bool:
             # Check PDF version
             # Verify not corrupted
             # Check if encrypted
             # Validate content structure
             pass
     ```

  5. Text Processing Pipeline:
     - Pre-processing:
       * Remove headers/footers
       * Handle page breaks
       * Clean special characters
       * Normalize whitespace
     - Content Extraction:
       * Identify section boundaries
       * Extract tables
       * Preserve formatting hints
       * Handle columns/layouts
     - Post-processing:
       * Merge split lines
       * Fix hyphenation
       * Standardize bullets/numbering
       * Clean up artifacts

  6. Error Handling:
     - Common PDF Issues:
       * Corrupted files
       * Password protection
       * Scanned images
       * Malformed structure
     - Recovery Strategies:
       * OCR fallback
       * Alternative parsing methods
       * Manual intervention flags
       * Error documentation

  7. Performance Optimization:
     - Caching:
       * Store extracted text
       * Cache parsed tables
       * Save processed results
     - Resource Management:
       * Close file handles
       * Memory cleanup
       * Batch processing
       * Progress tracking

  8. Quality Assurance:
     - Validation Checks:
       * Text extraction completeness
       * Table structure integrity
       * Pattern matching accuracy
       * Content preservation
     - Reporting:
       * Extraction statistics
       * Error summaries
       * Processing time
       * Success rates
  </IMPORTANT_NOTES>

### Additional Carriers
- [x] **Story 2.2: Cigna Implementation**
  - Research Cigna's portal structure
  - Implement Cigna-specific spider
  - Create custom parsing rules
  - Test extraction accuracy
  - AC: Successfully extracts Cigna guidelines

  <IMPORTANT_NOTES>
  1. Spider Configuration:
     ```python
     class CignaSpider(InsuranceSpider):
         name = 'cigna'
         allowed_domains = ['cigna.com']
         carrier_name = 'Cigna'
         base_url = 'https://www.cigna.com/healthcare-providers/resources-for-health-care-professionals/dental'
         pdf_enabled = True
         
         custom_settings = {
             'CONCURRENT_REQUESTS': 2,
             'DOWNLOAD_DELAY': 3,
             'ROBOTSTXT_OBEY': True,
             'DOWNLOAD_TIMEOUT': 60
         }
     ```


  2. PDF Processing Customization:
     ```python
     class CignaPDFProcessor(PDFProcessor):
         def __init__(self):
             super().__init__()
             self.cigna_specific_patterns = {
                 'section_header': r'(?:Section|Category):\s*(.*?)(?:\n|$)',
                 'procedure_block': r'(?m)^D\d{4}.*?(?=^D\d{4}|\Z)',
                 'requirement_list': r'(?:Required Documentation|Documentation Requirements):[\s\S]*?(?=\n\n|\Z)'
             }

         def extract_requirements(self, text: str) -> List[str]:
             # Handle Cigna's specific bullet point format
             # Extract nested requirements
             # Process conditional requirements
             pass
     ```

  3. Document Structure:
     - Main Sections:
       * General Information
       * Procedure Categories
       * Documentation Requirements
       * Special Considerations
     - Subsections:
       * By Procedure Type
       * By Insurance Plan
       * By Geographic Region

  4. Data Extraction Rules:
     - CDT Code Format:
       * Standard D-code format
       * Include subcategories
       * Handle procedure variations
     - Requirements:
       * Primary documentation
       * Alternative documentation
       * Conditional requirements
       * Time-based requirements

  5. Validation Rules:
     ```python
     class CignaValidator:
         def validate_procedure(self, proc: Procedure) -> bool:
             # Verify against Cigna's procedure list
             # Check required fields presence
             # Validate documentation requirements
             # Verify plan-specific rules
             pass

         def validate_requirements(self, reqs: List[str]) -> bool:
             # Check format consistency
             # Verify completeness
             # Validate against templates
             # Check for required elements
             pass
     ```

  6. Special Handling:
     - Plan-Specific Rules:
       * DHMO vs. DPPO differences
       * State-specific requirements
       * Network-specific rules
     - Documentation Types:
       * Clinical notes
       * Radiographs
       * Photographs
       * Narrative requirements

  7. Error Recovery:
     - Common Issues:
       * Missing procedure codes
       * Incomplete requirements
       * Ambiguous documentation
       * Format inconsistencies
     - Resolution Steps:
       * Pattern matching fallbacks
       * Alternative section detection
       * Manual review flags
       * Error documentation

  8. Quality Checks:
     - Completeness:
       * All procedures found
       * Requirements extracted
       * Notes captured
       * Metadata present
     - Accuracy:
       * Format validation
       * Cross-reference with 2024
       * Plan-specific verification
       * Documentation completeness
  </IMPORTANT_NOTES>

- [x] **Story 2.3: MetLife Implementation**
  - Research MetLife's portal structure
  - Implement MetLife-specific spider
  - Create custom parsing rules
  - Test extraction accuracy
  - AC: Successfully extracts MetLife guidelines

  <IMPORTANT_NOTES>
  1. Spider Configuration:
     ```python
     class MetLifeSpider(InsuranceSpider):
         name = 'metlife'
         allowed_domains = ['metlife.com', 'metdental.com']
         carrier_name = 'MetLife'
         base_url = 'https://www.metlife.com/dental-providers/resources/'
         pdf_enabled = True
         
         custom_settings = {
             'CONCURRENT_REQUESTS': 2,
             'DOWNLOAD_DELAY': 3,
             'ROBOTSTXT_OBEY': True,
             'DOWNLOAD_TIMEOUT': 60,
             'COOKIES_ENABLED': True
         }
     ```

  2. Document Processing:
     ```python
     class MetLifePDFProcessor(PDFProcessor):
         def __init__(self):
             super().__init__()
             self.metlife_patterns = {
                 'procedure_start': r'Procedure\s+(?:Code|Guidelines):\s*D\d{4}',
                 'documentation_block': r'Required\s+Documentation:.*?(?=Procedure|$)',
                 'special_notes': r'Special\s+Considerations:.*?(?=\n\n|\Z)'
             }
             
         def process_documentation(self, text: str) -> Dict[str, List[str]]:
             # Extract documentation requirements
             # Handle MetLife-specific formats
             # Process conditional requirements
             pass
     ```

  3. MetLife-Specific Features:
     - Document Categories:
       * Clinical Guidelines
       * Documentation Requirements
       * Pre-authorization Rules
       * Payment Policies
     - Plan Types:
       * PDP Plus
       * SafeGuard
       * Federal Dental
       * TakeAlong Dental

  4. Parsing Rules:
     - Section Identification:
       * Procedure code blocks
       * Documentation sections
       * Clinical criteria
       * Frequency limitations
     - Content Extraction:
       * Required x-rays
       * Clinical documentation
       * Time requirements
       * Alternative procedures

  5. Data Transformation:
     ```python
     class MetLifeTransformer:
         def standardize_requirements(self, raw_reqs: List[str]) -> List[str]:
             # Convert MetLife format to standard
             # Handle special cases
             # Normalize terminology
             # Sort by importance
             pass

         def process_special_notes(self, notes: str) -> Dict:
             # Extract relevant information
             # Categorize notes
             # Handle plan-specific details
             pass
     ```

  6. Validation Framework:
     - Document Checks:
       * Version verification
       * Completeness check
       * Format validation
       * Cross-reference with standards
     - Content Validation:
       * Required fields present
       * Consistent terminology
       * Valid procedure codes
       * Complete requirements

  7. Error Handling:
     - Common Scenarios:
       * PDF format changes
       * Missing sections
       * Inconsistent formatting
       * Invalid procedure codes
     - Recovery Actions:
       * Alternative parsing methods
       * Section reconstruction
       * Format normalization
       * Error logging

  8. Quality Assurance:
     - Automated Checks:
       * Procedure code validation
       * Requirements completeness
       * Format consistency
       * Data integrity
     - Manual Review Flags:
       * Unusual patterns
       * Missing information
       * Format anomalies
       * Version discrepancies

  9. Performance Considerations:
     - Processing Optimization:
       * Batch processing
       * Caching strategies
       * Memory management
       * Progress tracking
     - Resource Management:
       * File handle cleanup
       * Memory usage monitoring
       * Concurrent processing
       * Error recovery

  10. Python 3.13 Compatibility:
      - Python 3.13 removed the `cgi` module which Scrapy depends on
      - Install the legacy-cgi package as a drop-in replacement:
        ```
        pip install legacy-cgi
        ```
      - No code changes are needed after installing this package
      - This package is maintained specifically to address this compatibility issue
      - Used by hundreds of projects as the standard solution for Python 3.13+ compatibility
  </IMPORTANT_NOTES>

- [ ] **Story 2.4: United Healthcare Implementation**
  - Research UHC's portal structure
  - Implement UHC-specific spider
  - Create custom parsing rules
  - Test extraction accuracy
  - AC: Successfully extracts UHC guidelines

  <IMPORTANT_NOTES>
  1. Spider Configuration:
     ```python
     class UHCSpider(InsuranceSpider):
         name = 'uhc'
         allowed_domains = ['uhc.com', 'unitedhealthcareonline.com']
         carrier_name = 'UnitedHealthcare'
         base_url = 'https://www.uhc.com/dental-providers/policies-and-guidelines'
         pdf_enabled = True
         
         custom_settings = {
             'CONCURRENT_REQUESTS': 2,
             'DOWNLOAD_DELAY': 3,
             'ROBOTSTXT_OBEY': True,
             'DOWNLOAD_TIMEOUT': 60,
             'COOKIES_ENABLED': True
         }
     ```

  2. Document Structure:
     ```python
     class UHCPDFProcessor(PDFProcessor):
         def __init__(self):
             super().__init__()
             self.uhc_patterns = {
                 'policy_number': r'Policy\s+Number:\s*(\w+)',
                 'effective_date': r'Effective\s+Date:\s*(\d{2}/\d{2}/\d{4})',
                 'cdt_section': r'(?m)^D\d{4}.*?(?=^D\d{4}|\Z)',
                 'documentation': r'Documentation\s+Required:.*?(?=\n\n|\Z)'
             }
             
         def extract_policy_details(self, text: str) -> Dict:
             # Extract policy metadata
             # Parse effective dates
             # Get coverage details
             # Handle policy updates
             pass
     ```

  3. UHC-Specific Features:
     - Document Types:
       * CDT Guidelines
       * Clinical Policies
       * Documentation Requirements
       * Network Rules
     - Policy Categories:
       * Commercial
       * Medicare Advantage
       * Medicaid
       * All Savers

  4. Data Extraction:
     - Section Processing:
       * Policy information
       * Procedure guidelines
       * Documentation requirements
       * Clinical criteria
     - Content Rules:
       * Required narratives
       * Image requirements
       * Time limitations
       * Coverage restrictions

  5. Validation System:
     ```python
     class UHCValidator:
         def validate_policy(self, policy: Dict) -> bool:
             # Check policy number format
             # Verify effective dates
             # Validate coverage types
             # Check documentation rules
             pass

         def validate_requirements(self, requirements: List[str]) -> bool:
             # Verify documentation completeness
             # Check format consistency
             # Validate against standards
             # Ensure all required elements
             pass
     ```

  6. Special Processing:
     - Plan Variations:
       * Different documentation by plan
       * State-specific requirements
       * Network tier variations
       * Special program rules
     - Documentation Types:
       * Clinical records
       * Radiographs
       * Photographs
       * Written narratives

  7. Error Management:
     - Common Issues:
       * Policy updates
       * Format changes
       * Missing sections
       * Inconsistent structure
     - Resolution Steps:
       * Alternative parsing
       * Update detection
       * Manual review flags
       * Error documentation

  8. Quality Control:
     - Automated Verification:
       * Policy number validation
       * Date format checking
       * Requirement completeness
       * Format consistency
     - Manual Review Triggers:
       * New policy formats
       * Requirement changes
       * Unusual patterns
       * Version conflicts

  9. Performance Optimization:
     - Processing:
       * Parallel processing
       * Caching strategy
       * Memory management
       * Progress tracking
     - Resource Handling:
       * File cleanup
       * Memory monitoring
       * Connection pooling
       * Error recovery

  10. Integration Points:
      - Systems:
        * Policy database
        * Provider portal
        * Claims system
        * Documentation system
      - Data Flow:
        * Policy updates
        * Requirement changes
        * Coverage modifications
        * Format revisions
  </IMPORTANT_NOTES>

### Data Processing
- [x] **Story 2.5: Data Cleaning Module**
  - Design data cleaning pipeline
  - Implement text normalization
  - Create validation rules
  - Add error handling
  - AC: Clean and standardized data output

  <IMPORTANT_NOTES>
  1. Data Cleaning Pipeline:
     ```python
     class DataCleaningPipeline:
         def __init__(self):
             self.cleaners = [
                 WhitespaceNormalizer(),
                 TextStandardizer(),
                 CDTCodeCleaner(),
                 RequirementsCleaner(),
                 DateNormalizer()
             ]
             self.validators = [
                 DataCompleteness(),
                 FormatConsistency(),
                 ContentValidity()
             ]
         
         def process(self, data: Dict) -> Dict:
             # Apply each cleaner in sequence
             # Validate results
             # Log cleaning actions
             # Return cleaned data
             pass
     ```

  2. Text Normalization:
     ```python
     class TextStandardizer:
         def __init__(self):
             self.rules = {
                 'spacing': r'\s+',
                 'bullets': r'[•●■◆]',
                 'quotes': r'[""'']',
                 'dashes': r'[‒–—―]'
             }
             
         def standardize(self, text: str) -> str:
             # Replace unicode with ASCII
             # Normalize whitespace
             # Standardize punctuation
             # Fix common OCR errors
             pass
     ```

  3. CDT Code Processing:
     ```python
     class CDTCodeCleaner:
         def clean_code(self, code: str) -> str:
             # Remove spaces in codes
             # Validate format (D#### pattern)
             # Check against valid CDT codes
             # Handle deprecated codes
             pass
             
         def clean_description(self, desc: str) -> str:
             # Standardize terminology
             # Remove redundant text
             # Format consistently
             # Handle special cases
             pass
     ```

  4. Requirements Standardization:
     - Text Rules:
       * Remove redundant phrases
       * Standardize terminology
       * Format bullet points
       * Normalize lists
     - Content Rules:
       * Merge similar requirements
       * Remove duplicates
       * Sort by importance
       * Group related items

  5. Date and Time Handling:
     ```python
     class DateNormalizer:
         def __init__(self):
             self.date_formats = [
                 '%m/%d/%Y',
                 '%Y-%m-%d',
                 '%b %d, %Y',
                 '%d-%b-%Y'
             ]
             
         def normalize_date(self, date_str: str) -> str:
             # Parse various formats
             # Convert to standard format
             # Validate date ranges
             # Handle special cases
             pass
     ```

  6. Validation Framework:
     ```python
     class DataValidator:
         def validate_structure(self, data: Dict) -> bool:
             # Check required fields
             # Validate data types
             # Verify relationships
             # Ensure completeness
             pass
             
         def validate_content(self, data: Dict) -> bool:
             # Check value ranges
             # Verify consistency
             # Validate references
             # Check business rules
             pass
     ```

  7. Error Recovery:
     - Detection:
       * Missing data
       * Invalid formats
       * Inconsistent values
       * Business rule violations
     - Resolution:
       * Default values
       * Format correction
       * Value normalization
       * Manual review flags

  8. Quality Metrics:
     - Completeness:
       * Required fields present
       * No missing values
       * Valid relationships
       * Complete context
     - Accuracy:
       * Correct formats
       * Valid values
       * Consistent data
       * Business rule compliance

  9. Performance Considerations:
     - Processing:
       * Batch processing
       * Incremental updates
       * Parallel cleaning
       * Progress tracking
     - Resource Management:
       * Memory efficiency
       * CPU optimization
       * Storage handling
       * Cache utilization

  10. Integration:
      - Input Sources:
        * Raw spider data
        * PDF extracts
        * Manual entries
        * External feeds
      - Output Formats:
        * JSON structure
        * CSV exports
        * Database records
        * API responses
  </IMPORTANT_NOTES>

## Sprint 3: Testing & Refinement (Day 2-3)

### Testing
- [x] **Story 3.1: Unit Test Suite**
  - Set up testing framework
  - Write core component tests
  - Add mock responses
  - Create test data
  - AC: 80% test coverage achieved

  <IMPORTANT_NOTES>
  1. Test Framework Setup:
     ```python
     # conftest.py
     import pytest
     from unittest.mock import Mock, patch
     from typing import Dict, List
     
     @pytest.fixture
     def mock_spider():
         return Mock(
             name='test_spider',
             allowed_domains=['test.com'],
             start_urls=['https://test.com/start'],
             custom_settings={'ROBOTSTXT_OBEY': False}
         )
     
     @pytest.fixture
     def sample_pdf_content():
         return {
             'text': 'Sample PDF content with D0150 code',
             'metadata': {'Title': 'Test PDF', 'Author': 'Test'}
         }
     
     @pytest.fixture
     def mock_response():
         return Mock(
             url='https://test.com/doc.pdf',
             body=b'PDF content',
             headers={'content-type': 'application/pdf'}
         )
     ```

  2. Core Component Tests:
     ```python
     class TestPDFExtractor:
         def test_text_extraction(self, sample_pdf_content):
             extractor = PDFExtractor()
             result = extractor.extract_text(sample_pdf_content)
             assert 'D0150' in result
             
         def test_table_parsing(self, sample_pdf_content):
             extractor = PDFExtractor()
             tables = extractor.extract_tables(sample_pdf_content)
             assert len(tables) > 0
             
     class TestDataCleaning:
         def test_cdt_code_cleaning(self):
             cleaner = CDTCodeCleaner()
             result = cleaner.clean_code('D 0150')
             assert result == 'D0150'
             
         def test_requirement_cleaning(self):
             cleaner = RequirementsCleaner()
             result = cleaner.clean('Required: X-rays • Photos')
             assert '•' not in result
     ```

  3. Spider Tests:
     ```python
     class TestBaseSpider:
         def test_start_requests(self, mock_spider):
             requests = list(mock_spider.start_requests())
             assert len(requests) > 0
             
         def test_parse_pdf(self, mock_spider, mock_response):
             result = mock_spider.parse_pdf(mock_response)
             assert result['url'] == mock_response.url
             
     class TestCarrierSpiders:
         @pytest.mark.parametrize('carrier', ['aetna', 'cigna', 'metlife', 'uhc'])
         def test_carrier_specific_parsing(self, carrier):
             spider = get_spider_class(carrier)()
             assert spider.name == carrier
     ```

  4. Mock Data Structure:
     - PDF Samples:
       * Clean format examples
       * Edge cases
       * Error conditions
       * Different layouts
     - Response Types:
       * Success responses
       * Error responses
       * Timeout scenarios
       * Rate limit responses

  5. Coverage Requirements:
     - Core Components:
       * PDF extraction (90%)
       * Data cleaning (85%)
       * Validation (85%)
       * Spider logic (80%)
     - Edge Cases:
       * Error handling
       * Invalid inputs
       * Boundary conditions
       * Resource limits

  6. Test Categories:
     ```python
     @pytest.mark.extraction
     class TestExtractionFeatures:
         # PDF extraction tests
         # Table parsing tests
         # Text processing tests
         pass
         
     @pytest.mark.cleaning
     class TestDataCleaning:
         # Normalization tests
         # Validation tests
         # Error handling tests
         pass
         
     @pytest.mark.integration
     class TestComponentIntegration:
         # Pipeline tests
         # System flow tests
         # Error propagation tests
         pass
     ```

  7. Performance Tests:
     ```python
     class TestPerformance:
         @pytest.mark.benchmark
         def test_pdf_extraction_speed(self, benchmark):
             def extract():
                 extractor = PDFExtractor()
                 extractor.process_file('sample.pdf')
             benchmark(extract)
             
         @pytest.mark.benchmark
         def test_data_cleaning_speed(self, benchmark):
             def clean():
                 cleaner = DataCleaningPipeline()
                 cleaner.process(sample_data)
             benchmark(clean)
     ```

  8. Error Handling Tests:
     ```python
     class TestErrorHandling:
         def test_corrupted_pdf(self):
             with pytest.raises(PDFError):
                 extractor = PDFExtractor()
                 extractor.process_file('corrupted.pdf')
                 
         def test_invalid_data(self):
             with pytest.raises(ValidationError):
                 validator = DataValidator()
                 validator.validate({'invalid': 'data'})
     ```

  9. Mocking Strategy:
     - External Services:
       * PDF processing
       * Network requests
       * File operations
       * Database calls
     - Test Data:
       * Representative samples
       * Edge cases
       * Error conditions
       * Special formats

  10. CI/CD Integration:
      - Pipeline Steps:
        * Run unit tests
        * Check coverage
        * Performance tests
        * Integration tests
      - Quality Gates:
        * Coverage thresholds
        * Performance benchmarks
        * Error rates
        * Code quality
  </IMPORTANT_NOTES>

- [x] **Story 3.2: Integration Testing**
  - End-to-end test framework
  - Pipeline components integration tests
  - Carrier-specific integration tests
  - Data flow validation
  - Mock service integration
  - Error scenario testing
  - Performance integration tests
  - Data consistency checks
  - System integration tests
  - Quality assurance
  - AC: All integration points tested

  <IMPORTANT_NOTES>
  1. End-to-End Test Framework:
     ```python
     # test_integration.py
     import pytest
     from typing import Dict, List
     from unittest.mock import patch
     
     class TestEndToEndPipeline:
         @pytest.fixture(autouse=True)
         def setup(self):
             self.pipeline = ExtractionPipeline(
                 spider_manager=SpiderManager(),
                 pdf_processor=PDFProcessor(),
                 data_cleaner=DataCleaner(),
                 validator=DataValidator()
             )
             
         @pytest.mark.integration
         def test_full_pipeline(self):
             input_data = {'url': 'test.com/doc.pdf'}
             result = self.pipeline.process(input_data)
             assert result['status'] == 'success'
             assert 'extracted_data' in result
     ```

  2. Pipeline Components Integration:
     ```python
     class TestComponentInteractions:
         def test_spider_to_processor(self):
             # Test data flow from spider to PDF processor
             spider = TestSpider()
             processor = PDFProcessor()
             result = processor.process(spider.fetch())
             assert result.is_valid()
             
         def test_processor_to_cleaner(self):
             # Test data flow from processor to cleaner
             processor = PDFProcessor()
             cleaner = DataCleaner()
             result = cleaner.clean(processor.output)
             assert result.is_normalized()
     ```

  3. Carrier-Specific Integration:
     ```python
     @pytest.mark.parametrize('carrier', [
         'aetna',
         'cigna',
         'metlife',
         'uhc'
     ])
     class TestCarrierIntegration:
         def test_carrier_pipeline(self, carrier):
             spider = get_spider(carrier)
             pipeline = get_pipeline(carrier)
             result = pipeline.process(spider.start())
             assert result['carrier'] == carrier
             assert result['status'] == 'success'
     ```

  4. Data Flow Validation:
     - Pipeline Stages:
       * Spider crawling
       * PDF extraction
       * Data cleaning
       * Validation
     - Checkpoints:
       * Data integrity
       * Format consistency
       * Error propagation
       * State management

  5. Mock Service Integration:
     ```python
     class MockServices:
         @pytest.fixture
         def mock_pdf_service(self):
             with patch('services.pdf.PDFService') as mock:
                 mock.extract.return_value = {
                     'text': 'Sample text',
                     'metadata': {'pages': 1}
                 }
                 yield mock
                 
         @pytest.fixture
         def mock_database(self):
             with patch('services.db.Database') as mock:
                 mock.save.return_value = True
                 yield mock
     ```

  6. Error Scenario Testing:
     ```python
     class TestErrorScenarios:
         def test_network_failure(self):
             with patch('services.network.fetch') as mock:
                 mock.side_effect = NetworkError
                 result = self.pipeline.process({})
                 assert result['status'] == 'error'
                 assert 'network_error' in result['errors']
                 
         def test_invalid_pdf(self):
             with patch('services.pdf.extract') as mock:
                 mock.side_effect = PDFError
                 result = self.pipeline.process({})
                 assert result['status'] == 'error'
                 assert 'pdf_error' in result['errors']
     ```

  7. Performance Integration:
     ```python
     class TestPipelinePerformance:
         @pytest.mark.benchmark
         def test_pipeline_throughput(self, benchmark):
             def process_batch():
                 pipeline = ExtractionPipeline()
                 pipeline.process_batch(test_data)
             benchmark(process_batch)
             
         def test_resource_usage(self):
             monitor = ResourceMonitor()
             with monitor:
                 self.pipeline.process(test_data)
             assert monitor.peak_memory < MEMORY_LIMIT
             assert monitor.execution_time < TIME_LIMIT
     ```

  8. Data Consistency Checks:
     - Cross-Component Validation:
       * Field presence
       * Type consistency
       * Value ranges
       * Relationships
     - State Verification:
       * Pipeline state
       * Component state
       * Resource state
       * System state

  9. System Integration:
     ```python
     class TestSystemIntegration:
         def test_database_integration(self):
             pipeline = ExtractionPipeline()
             db = Database()
             result = pipeline.process_and_save(test_data, db)
             assert db.verify(result['id'])
             
         def test_api_integration(self):
             pipeline = ExtractionPipeline()
             api = APIClient()
             result = pipeline.process_and_send(test_data, api)
             assert api.verify_sent(result['id'])
     ```

  10. Quality Assurance:
      - Validation Points:
        * Data accuracy
        * Format compliance
        * Business rules
        * System health
      - Monitoring:
        * Performance metrics
        * Error rates
        * Resource usage
        * System stability
  </IMPORTANT_NOTES>

### Refinement
- [ ] **Story 3.3: Performance Optimization**
  - Profile system performance
  - Optimize memory usage
  - Implement caching
  - Add parallel processing
  - AC: Response time under 2s per page

  <IMPORTANT_NOTES>
  1. Performance Profiling:
     ```python
     # profiler.py
     import cProfile
     import memory_profiler
     from typing import Dict, List
     
     class PerformanceProfiler:
         def __init__(self):
             self.profiler = cProfile.Profile()
             self.memory_tracker = memory_profiler.profile
             
         def profile_function(self, func, *args, **kwargs):
             self.profiler.enable()
             result = func(*args, **kwargs)
             self.profiler.disable()
             return result
             
         @memory_tracker
         def track_memory(self, func, *args, **kwargs):
             return func(*args, **kwargs)
     ```

  2. Memory Optimization:
     ```python
     class MemoryOptimizedPipeline:
         def __init__(self):
             self.chunk_size = 1024 * 1024  # 1MB chunks
             self.max_buffer = 10  # Max items in memory
             
         def process_large_pdf(self, file_path: str):
             with open(file_path, 'rb') as f:
                 while chunk := f.read(self.chunk_size):
                     yield self.process_chunk(chunk)
                     
         def clean_memory(self):
             import gc
             gc.collect()
             self.clear_cache()
     ```

  3. Caching Implementation:
     ```python
     from functools import lru_cache
     import redis
     
     class CacheManager:
         def __init__(self):
             self.redis = redis.Redis()
             self.ttl = 3600  # 1 hour
             
         @lru_cache(maxsize=100)
         def get_pdf_content(self, url: str) -> Dict:
             return self._fetch_content(url)
             
         def cache_result(self, key: str, value: Dict):
             self.redis.setex(
                 key,
                 self.ttl,
                 json.dumps(value)
             )
     ```

  4. Parallel Processing:
     ```python
     from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
     
     class ParallelProcessor:
         def __init__(self):
             self.max_workers = cpu_count()
             self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
             self.process_pool = ProcessPoolExecutor(max_workers=self.max_workers)
             
         def process_batch(self, items: List[Dict]):
             futures = []
             for item in items:
                 future = self.process_pool.submit(
                     self.process_item,
                     item
                 )
                 futures.append(future)
             return [f.result() for f in futures]
     ```

  5. Resource Management:
     - Memory Limits:
       * PDF buffer size
       * Cache size
       * Queue length
       * Thread pools
     - CPU Usage:
       * Worker count
       * Process limits
       * Task priority
       * Load balancing

  6. Database Optimization:
     ```python
     class OptimizedDatabase:
         def __init__(self):
             self.batch_size = 100
             self.indexes = ['carrier', 'cdt_code']
             
         def bulk_insert(self, records: List[Dict]):
             for i in range(0, len(records), self.batch_size):
                 batch = records[i:i + self.batch_size]
                 self.db.insert_many(batch)
                 
         def optimize_queries(self):
             self.db.create_indexes(self.indexes)
     ```

  7. Network Optimization:
     ```python
     class NetworkOptimizer:
         def __init__(self):
             self.connection_pool = ConnectionPool(max_size=100)
             self.timeout = 30
             
         async def fetch_concurrent(self, urls: List[str]):
             async with aiohttp.ClientSession() as session:
                 tasks = []
                 for url in urls:
                     task = asyncio.create_task(
                         self.fetch_url(session, url)
                     )
                     tasks.append(task)
                 return await asyncio.gather(*tasks)
     ```

  8. PDF Processing Optimization:
     ```python
     class OptimizedPDFProcessor:
         def __init__(self):
             self.page_chunk_size = 5
             self.preprocess_enabled = True
             
         def process_large_pdf(self, pdf_path: str):
             reader = PdfReader(pdf_path)
             for i in range(0, len(reader.pages), self.page_chunk_size):
                 pages = reader.pages[i:i + self.page_chunk_size]
                 yield self.process_pages(pages)
                 
         def optimize_extraction(self, page):
             if self.preprocess_enabled:
                 page = self.preprocess_page(page)
             return self.extract_text(page)
     ```

  9. Monitoring and Metrics:
     ```python
     class PerformanceMonitor:
         def __init__(self):
             self.metrics = {
                 'response_time': [],
                 'memory_usage': [],
                 'cpu_usage': [],
                 'error_rate': []
             }
             
         def record_metric(self, metric: str, value: float):
             self.metrics[metric].append({
                 'value': value,
                 'timestamp': time.time()
             })
             
         def get_statistics(self):
             return {
                 metric: statistics.mean(m['value'] 
                     for m in values[-100:])
                 for metric, values in self.metrics.items()
             }
     ```

  10. Performance Targets:
      - Response Times:
        * PDF extraction < 1s
        * Data cleaning < 0.5s
        * API response < 2s
        * Total pipeline < 5s
      - Resource Usage:
        * Memory < 500MB
        * CPU < 70%
        * Network < 1000 req/min
        * Storage < 1GB/day
  </IMPORTANT_NOTES>

- [ ] **Story 3.4: Error Recovery**
  - Implement retry mechanism
  - Add error logging
  - Create recovery strategies
  - Set up monitoring
  - AC: System recovers from common failures

  <IMPORTANT_NOTES>
  1. Error Handling Framework:
     ```python
     # error_handler.py
     from typing import Dict, List, Optional
     import logging
     from enum import Enum
     
     class ErrorSeverity(Enum):
         LOW = 1
         MEDIUM = 2
         HIGH = 3
         CRITICAL = 4
         
     class ErrorHandler:
         def __init__(self):
             self.logger = logging.getLogger(__name__)
             self.recovery_strategies = {}
             self.error_counts = {}
             
         def handle_error(self, error: Exception, context: Dict) -> Optional[Dict]:
             severity = self.classify_error(error)
             self.log_error(error, severity, context)
             return self.apply_recovery_strategy(error, severity)
     ```

  2. Retry Mechanism:
     ```python
     from tenacity import retry, stop_after_attempt, wait_exponential
     
     class RetryManager:
         def __init__(self):
             self.max_attempts = 3
             self.wait_multiplier = 2
             
         @retry(
             stop=stop_after_attempt(3),
             wait=wait_exponential(multiplier=2),
             retry=retry_if_exception_type(RetryableError)
         )
         def retry_operation(self, func, *args, **kwargs):
             try:
                 return func(*args, **kwargs)
             except Exception as e:
                 self.log_retry_attempt(e)
                 raise
     ```

  3. Error Logging System:
     ```python
     class ErrorLogger:
         def __init__(self):
             self.logger = logging.getLogger(__name__)
             self.setup_logging()
             
         def log_error(self, error: Exception, context: Dict):
             self.logger.error(
                 "Error occurred",
                 extra={
                     'error_type': type(error).__name__,
                     'error_message': str(error),
                     'context': context,
                     'stack_trace': traceback.format_exc()
                 }
             )
             
         def setup_logging(self):
             # Configure logging handlers
             # Set up log rotation
             # Define log format
             # Set up alerts
             pass
     ```

  4. Recovery Strategies:
     ```python
     class RecoveryStrategy:
         def __init__(self):
             self.strategies = {
                 NetworkError: self.handle_network_error,
                 PDFError: self.handle_pdf_error,
                 ValidationError: self.handle_validation_error,
                 DatabaseError: self.handle_database_error
             }
             
         async def handle_network_error(self, context: Dict):
             # Implement exponential backoff
             # Check alternative endpoints
             # Verify network status
             # Update connection pool
             pass
             
         def handle_pdf_error(self, context: Dict):
             # Try alternative PDF library
             # Check file integrity
             # Attempt repair
             # Log unrecoverable cases
             pass
     ```

  5. Monitoring Setup:
     ```python
     class ErrorMonitor:
         def __init__(self):
             self.alert_thresholds = {
                 ErrorSeverity.LOW: 100,
                 ErrorSeverity.MEDIUM: 50,
                 ErrorSeverity.HIGH: 10,
                 ErrorSeverity.CRITICAL: 1
             }
             
         def check_error_rates(self):
             for severity, count in self.error_counts.items():
                 if count >= self.alert_thresholds[severity]:
                     self.trigger_alert(severity, count)
                     
         def generate_error_report(self):
             return {
                 'error_counts': self.error_counts,
                 'error_rates': self.calculate_rates(),
                 'top_errors': self.get_top_errors()
             }
     ```

  6. Circuit Breaker:
     ```python
     class CircuitBreaker:
         def __init__(self):
             self.failure_threshold = 5
             self.reset_timeout = 60
             self.state = 'closed'
             
         def execute(self, func, *args, **kwargs):
             if self.state == 'open':
                 if self.should_reset():
                     self.half_open()
                 else:
                     raise CircuitBreakerOpen()
                     
             try:
                 result = func(*args, **kwargs)
                 self.record_success()
                 return result
             except Exception as e:
                 self.record_failure()
                 raise
     ```

  7. Data Recovery:
     ```python
     class DataRecovery:
         def __init__(self):
             self.backup_manager = BackupManager()
             self.checkpoint_interval = 100
             
         def create_checkpoint(self, data: Dict):
             self.backup_manager.save_checkpoint({
                 'data': data,
                 'timestamp': time.time(),
                 'metadata': self.get_metadata()
             })
             
         def restore_from_checkpoint(self):
             latest_checkpoint = self.backup_manager.get_latest()
             return self.restore_data(latest_checkpoint)
     ```

  8. Health Checks:
     ```python
     class SystemHealth:
         def __init__(self):
             self.checks = {
                 'database': self.check_database,
                 'network': self.check_network,
                 'pdf_service': self.check_pdf_service,
                 'cache': self.check_cache
             }
             
         async def run_health_checks(self):
             results = {}
             for name, check in self.checks.items():
                 try:
                     results[name] = await check()
                 except Exception as e:
                     results[name] = {
                         'status': 'failed',
                         'error': str(e)
                     }
             return results
     ```

  9. Error Prevention:
     - Input Validation:
       * Schema validation
       * Type checking
       * Range validation
       * Format verification
     - Resource Checks:
       * Memory availability
       * Disk space
       * Network connectivity
       * Service health

  10. Recovery Workflow:
      - Detection Phase:
        * Error identification
        * Context gathering
        * Impact assessment
        * Priority assignment
      - Recovery Phase:
        * Strategy selection
        * Action execution
        * Verification
        * Reporting
  </IMPORTANT_NOTES>

## Sprint 4: Final Data Collection & Documentation (Day 3)

### Data Collection
- [ ] **Story 4.1: Full Data Extraction**
  - Run extraction for all carriers
  - Validate collected data
  - Generate summary statistics
  - Create data quality report
  - AC: Complete dataset collected for all carriers

- [ ] **Story 4.2: Final Data Collection**
  - Run all carrier spiders
  - Validate collected data
  - Generate reports
  - Archive results
  - AC: Complete dataset collected

  <IMPORTANT_NOTES>
  1. Data Collection Orchestration:
     ```python
     # collection_manager.py
     from typing import Dict, List
     import asyncio
     from datetime import datetime
     
     class DataCollectionManager:
         def __init__(self):
             self.carriers = ['aetna', 'cigna', 'metlife', 'uhc']
             self.spiders = self.initialize_spiders()
             self.validators = self.initialize_validators()
             
         async def run_collection(self):
             tasks = [
                 self.collect_carrier_data(carrier)
                 for carrier in self.carriers
             ]
             return await asyncio.gather(*tasks)
     ```

  2. Validation Pipeline:
     ```python
     class DataValidationPipeline:
         def __init__(self):
             self.validation_steps = [
                 self.validate_structure,
                 self.validate_content,
                 self.validate_relationships,
                 self.validate_completeness
             ]
             
         def validate_dataset(self, data: Dict) -> Dict:
             results = {}
             for step in self.validation_steps:
                 result = step(data)
                 results[step.__name__] = result
             return self.generate_validation_report(results)
     ```

  3. Report Generation:
     ```python
     class ReportGenerator:
         def __init__(self):
             self.report_types = {
                 'coverage': self.generate_coverage_report,
                 'quality': self.generate_quality_report,
                 'statistics': self.generate_statistics_report,
                 'issues': self.generate_issues_report
             }
             
         def generate_all_reports(self, data: Dict):
             timestamp = datetime.now().isoformat()
             return {
                 report_type: generator(data, timestamp)
                 for report_type, generator in self.report_types.items()
             }
     ```

  4. Data Archival:
     ```python
     class DataArchiver:
         def __init__(self):
             self.storage_path = 'archives/'
             self.compression_level = 9
             self.retention_days = 30
             
         def archive_dataset(self, data: Dict, metadata: Dict):
             archive_name = self.generate_archive_name(metadata)
             self.compress_data(data, archive_name)
             self.store_metadata(metadata, archive_name)
             self.cleanup_old_archives()
     ```

  5. Quality Metrics:
     ```python
     class QualityAnalyzer:
         def __init__(self):
             self.metrics = {
                 'completeness': self.measure_completeness,
                 'accuracy': self.measure_accuracy,
                 'consistency': self.measure_consistency,
                 'timeliness': self.measure_timeliness
             }
             
         def analyze_quality(self, data: Dict) -> Dict:
             return {
                 metric: measure(data)
                 for metric, measure in self.metrics.items()
             }
     ```

  6. Data Statistics:
     ```python
     class DataStatistics:
         def __init__(self):
             self.statistics = {
                 'carrier_coverage': self.analyze_carrier_coverage,
                 'cdt_codes': self.analyze_cdt_codes,
                 'requirements': self.analyze_requirements,
                 'documentation': self.analyze_documentation
             }
             
         def generate_statistics(self, data: Dict) -> Dict:
             return {
                 stat: analyzer(data)
                 for stat, analyzer in self.statistics.items()
             }
     ```

  7. Issue Tracking:
     ```python
     class IssueTracker:
         def __init__(self):
             self.categories = {
                 'known_bugs': self.track_known_bugs,
                 'limitations': self.track_limitations,
                 'workarounds': self.track_workarounds,
                 'planned_fixes': self.track_planned_fixes
             }
             
         def track_issues(self, data: Dict) -> List[Dict]:
             issues = []
             for issue_type, tracker in self.categories.items():
                 issues.extend(tracker(data))
             return self.prioritize_issues(issues)
     ```

  8. Data Export:
     ```python
     class DataExporter:
         def __init__(self):
             self.export_formats = {
                 'json': self.export_json,
                 'csv': self.export_csv,
                 'excel': self.export_excel,
                 'xml': self.export_xml
             }
             
         def export_all_formats(self, data: Dict, path: str):
             results = {}
             for format_name, exporter in self.export_formats.items():
                 file_path = f"{path}/export.{format_name}"
                 results[format_name] = exporter(data, file_path)
             return results
     ```

  9. Verification Steps:
     - Data Integrity:
       * Checksum validation
       * Format verification
       * Relationship checks
       * Completeness tests
     - Quality Checks:
       * Coverage analysis
       * Accuracy metrics
       * Consistency review
       * Timeliness check

  10. Collection Summary:
      - Statistics:
        * Total records
        * Coverage metrics
        * Success rates
        * Error counts
      - Quality Metrics:
        * Completeness
        * Accuracy
        * Consistency
        * Timeliness
  </IMPORTANT_NOTES>

### Documentation
- [ ] **Story 4.3: Maintenance Documentation**
  - Document update procedures
  - Create monitoring guide
  - Add troubleshooting steps
  - Write enhancement plans
  - AC: Maintenance procedures documented

  <IMPORTANT_NOTES>
  1. Update Procedures:
     ```python
     # maintenance_guide.py
     from typing import Dict, List
     import yaml
     
     class MaintenanceGuide:
         def __init__(self):
             self.procedures = {
                 'daily': self.daily_tasks,
                 'weekly': self.weekly_tasks,
                 'monthly': self.monthly_tasks,
                 'quarterly': self.quarterly_tasks
             }
             
         def generate_procedures(self):
             return {
                 schedule: tasks()
                 for schedule, tasks in self.procedures.items()
             }
     ```

  2. Monitoring System:
     ```python
     class MonitoringSystem:
         def __init__(self):
             self.metrics = {
                 'system': self.system_metrics,
                 'performance': self.performance_metrics,
                 'data': self.data_metrics,
                 'errors': self.error_metrics
             }
             
         def setup_monitoring(self):
             return {
                 'prometheus': self.setup_prometheus(),
                 'grafana': self.setup_grafana(),
                 'alerts': self.setup_alerts(),
                 'logging': self.setup_logging()
             }
     ```

  3. Troubleshooting Guide:
     ```python
     class TroubleshootingGuide:
         def __init__(self):
             self.issues = {
                 'network': self.network_issues,
                 'parsing': self.parsing_issues,
                 'performance': self.performance_issues,
                 'data': self.data_issues
             }
             
         def generate_guide(self):
             return {
                 category: {
                     'symptoms': issue.symptoms(),
                     'diagnosis': issue.diagnosis(),
                     'solutions': issue.solutions()
                 }
                 for category, issue in self.issues.items()
             }
     ```

  4. System Updates:
     ```python
     class UpdateManager:
         def __init__(self):
             self.update_types = {
                 'carrier_changes': self.handle_carrier_updates,
                 'dependency_updates': self.handle_dependency_updates,
                 'system_patches': self.handle_system_patches,
                 'security_updates': self.handle_security_updates
             }
             
         def update_procedure(self, update_type: str):
             handler = self.update_types.get(update_type)
             return {
                 'steps': handler.steps(),
                 'validation': handler.validation(),
                 'rollback': handler.rollback()
             }
     ```

  5. Performance Tuning:
     ```python
     class PerformanceTuning:
         def __init__(self):
             self.tuning_areas = {
                 'memory': self.memory_optimization,
                 'cpu': self.cpu_optimization,
                 'network': self.network_optimization,
                 'storage': self.storage_optimization
             }
             
         def generate_tuning_guide(self):
             return {
                 area: {
                     'metrics': tuner.metrics(),
                     'thresholds': tuner.thresholds(),
                     'actions': tuner.actions()
                 }
                 for area, tuner in self.tuning_areas.items()
             }
     ```

  6. Backup Procedures:
     ```python
     class BackupSystem:
         def __init__(self):
             self.backup_types = {
                 'full': self.full_backup,
                 'incremental': self.incremental_backup,
                 'differential': self.differential_backup,
                 'snapshot': self.snapshot_backup
             }
             
         def backup_procedures(self):
             return {
                 backup_type: {
                     'schedule': handler.schedule(),
                     'procedure': handler.procedure(),
                     'verification': handler.verify()
                 }
                 for backup_type, handler in self.backup_types.items()
             }
     ```

  7. Security Maintenance:
     ```python
     class SecurityMaintenance:
         def __init__(self):
             self.security_areas = {
                 'access_control': self.access_management,
                 'encryption': self.encryption_management,
                 'auditing': self.audit_management,
                 'compliance': self.compliance_management
             }
             
         def security_procedures(self):
             return {
                 area: {
                     'checks': handler.security_checks(),
                     'updates': handler.security_updates(),
                     'monitoring': handler.security_monitoring()
                 }
                 for area, handler in self.security_areas.items()
             }
     ```

  8. Disaster Recovery:
     ```python
     class DisasterRecovery:
         def __init__(self):
             self.recovery_scenarios = {
                 'data_loss': self.handle_data_loss,
                 'system_failure': self.handle_system_failure,
                 'security_breach': self.handle_security_breach,
                 'service_disruption': self.handle_service_disruption
             }
             
         def recovery_procedures(self):
             return {
                 scenario: {
                     'detection': handler.detect(),
                     'response': handler.respond(),
                     'recovery': handler.recover()
                 }
                 for scenario, handler in self.recovery_scenarios.items()
             }
     ```

  9. Enhancement Planning:
     - Future Improvements:
       * Performance optimization
       * Feature additions
       * Architecture updates
       * Integration expansions
     - Implementation:
       * Priority levels
       * Resource requirements
       * Timeline estimates
       * Risk assessment

  10. Documentation Updates:
      - Maintenance:
        * Regular reviews
        * Version control
        * Change tracking
        * Distribution
      - Content:
        * Technical details
        * User guides
        * API documentation
        * Training materials
  </IMPORTANT_NOTES>

### Final Delivery
- [ ] **Story 4.5: Project Handoff**
  - Prepare final deliverables
  - Create presentation of results
  - Document known limitations
  - Provide recommendations for Phase 2
  - AC: Project deliverables meet all PRD requirements

## Notes
- Each story is estimated at 1 story point
- Stories should be worked on sequentially within each sprint
- Daily standups to review progress and blockers
- Sprint reviews at the end of each day
- Documentation should be updated as stories are completed 

- [ ] **Story 4.4: Final Review & Handoff**
  - Conduct system review
  - Prepare handoff package
  - Train maintenance team
  - Document known issues
  - AC: System ready for production

  <IMPORTANT_NOTES>
  1. System Review Process:
     ```python
     # review_manager.py
     from typing import Dict, List
     from datetime import datetime
     
     class SystemReview:
         def __init__(self):
             self.review_areas = {
                 'architecture': self.review_architecture,
                 'performance': self.review_performance,
                 'security': self.review_security,
                 'reliability': self.review_reliability
             }
             
         def conduct_review(self) -> Dict:
             results = {}
             for area, reviewer in self.review_areas.items():
                 results[area] = reviewer()
             return self.generate_review_report(results)
     ```

  2. Handoff Package:
     ```python
     class HandoffPackage:
         def __init__(self):
             self.components = {
                 'documentation': self.prepare_documentation,
                 'source_code': self.prepare_source_code,
                 'configuration': self.prepare_configuration,
                 'deployment': self.prepare_deployment_guide
             }
             
         def generate_package(self) -> Dict:
             return {
                 component: preparer()
                 for component, preparer in self.components.items()
             }
     ```

  3. Training Materials:
     ```python
     class TrainingProgram:
         def __init__(self):
             self.modules = {
                 'system_overview': self.overview_module,
                 'operations': self.operations_module,
                 'troubleshooting': self.troubleshooting_module,
                 'maintenance': self.maintenance_module
             }
             
         def prepare_training(self) -> Dict:
             return {
                 module: content()
                 for module, content in self.modules.items()
             }
     ```

  4. Issue Documentation:
     ```python
     class IssueRegistry:
         def __init__(self):
             self.categories = {
                 'known_bugs': self.track_known_bugs,
                 'limitations': self.track_limitations,
                 'workarounds': self.track_workarounds,
                 'planned_fixes': self.track_planned_fixes
             }
             
         def compile_issues(self) -> Dict:
             return {
                 category: documenter()
                 for category, documenter in self.categories.items()
             }
     ```

  5. Quality Assurance:
     ```python
     class QualityAssurance:
         def __init__(self):
             self.checks = {
                 'code_quality': self.check_code_quality,
                 'test_coverage': self.check_test_coverage,
                 'documentation': self.check_documentation,
                 'performance': self.check_performance
             }
             
         def run_qa_checks(self) -> Dict:
             return {
                 check: checker()
                 for check, checker in self.checks.items()
             }
     ```

  6. Knowledge Transfer:
     ```python
     class KnowledgeTransfer:
         def __init__(self):
             self.areas = {
                 'architecture': self.transfer_architecture_knowledge,
                 'operations': self.transfer_operations_knowledge,
                 'maintenance': self.transfer_maintenance_knowledge,
                 'support': self.transfer_support_knowledge
             }
             
         def execute_transfer(self) -> Dict:
             return {
                 area: transfer()
                 for area, transfer in self.areas.items()
             }
     ```

  7. Production Readiness:
     ```python
     class ProductionReadiness:
         def __init__(self):
             self.checklist = {
                 'infrastructure': self.check_infrastructure,
                 'monitoring': self.check_monitoring,
                 'backup': self.check_backup,
                 'security': self.check_security
             }
             
         def verify_readiness(self) -> Dict:
             return {
                 item: check()
                 for item, check in self.checklist.items()
             }
     ```

  8. Support Transition:
     ```python
     class SupportTransition:
         def __init__(self):
             self.transition_steps = {
                 'documentation': self.transition_documentation,
                 'contacts': self.transition_contacts,
                 'procedures': self.transition_procedures,
                 'tools': self.transition_tools
             }
             
         def execute_transition(self) -> Dict:
             return {
                 step: transition()
                 for step, transition in self.transition_steps.items()
             }
     ```

  9. Final Verification:
     - System Health:
       * Component status
       * Performance metrics
       * Error rates
       * Resource usage
     - Documentation:
       * Completeness
       * Accuracy
       * Accessibility
       * Versioning

  10. Handoff Checklist:
      - Documentation:
        * System architecture
        * Operations manual
        * Troubleshooting guide
        * Contact information
      - Access:
        * Source code
        * Credentials
        * Tools
        * Resources
  </IMPORTANT_NOTES> 