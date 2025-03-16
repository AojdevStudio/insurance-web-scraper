# Product Requirements Document (PRD)
# Dental Insurance Guidelines Web Scraper

## 1. Project Overview

### 1.1 Background
Dental Narrator is an existing SaaS application that helps dental offices generate precise insurance claims using LLMs. The application currently uses 2024 insurance information and needs updating with 2025 guidelines to maintain accuracy. This project focuses specifically on creating a web scraping solution to collect updated dental insurance claims submission guidelines for major carriers.

### 1.2 Objectives
- Create a web scraper to download and extract 2025 dental insurance claims submission guidelines
- Focus on major dental PPO and Medicare Advantage plans
- Extract structured data about documentation requirements by procedure code
- Prepare the data for integration into a vector database for RAG implementation
- Complete the project within a 2-3 day timeframe

### 1.3 Success Metrics
- Successfully extract guidelines from at least 10 major carriers
- Structured data matches the format needed for Dental Narrator's RAG system
- Documentation is clear and organized by procedure code and carrier
- Project completed within the specified 2-3 day timeframe

## 2. Requirements

### 2.1 Target Data
The scraper should extract the following information:
- Procedure codes (CDT codes like D2542-D2544)
- Required documentation for each procedure (x-rays, photographs, narratives)
- Special notes and exceptions
- Metadata (carrier name, year, effective date if available)

### 2.2 Target Sources
Primary focus (Phase 1):
- Aetna 
- Cigna
- MetLife
- United Healthcare/Dental Benefit Providers
- Guardian
- Principal Financial Group
- Humana Dental
- Delta Dental (multiple state organizations)
- Blue Cross Blue Shield networks
- Ameritas

Secondary focus (Phase 2, if time permits):
- Medicare Advantage dental plans
- Additional carriers from the provided lists
- Third-party administrators (TPAs)

### 2.3 Technical Requirements
- Python-based solution utilizing Scrapy for web scraping
- PDF extraction capabilities using PyPDF2/pdfplumber
- Data storage in a structured format (JSON or CSV) ready for database import
- Docker environment for local development and testing
- Documentation of the scraping process for each carrier

## 3. Implementation Approach

### 3.1 Web Scraping Strategy
1. **Research Phase**:
   - Identify URL patterns for each carrier's provider resources
   - Document login requirements and access methods for each carrier
   - Map site structures to locate claims documentation guidelines

2. **Scraper Development**:
   - Create a base scraper class with common functionality
   - Develop carrier-specific spider modules for each insurance provider
   - Implement rate limiting and responsible scraping practices
   - Handle authentication where required

3. **PDF Processing**:
   - Extract text content from PDF documents
   - Implement pattern matching to identify procedure codes and requirements
   - Parse tables and structured content from PDFs
   - Handle variations in formatting across different carriers

### 3.2 Data Extraction Methods
The solution will employ multiple techniques depending on the source format:
- HTML parsing for web-based guidelines
- PDF text extraction for downloadable documents
- Table extraction for structured guidelines
- Regular expressions for identifying procedure codes and requirements
- Fallback to manual extraction for complex or protected sources

### 3.3 Data Model
All extracted data will be standardized into the following structure:
```json
{
  "carrier": "Carrier Name",
  "year": "2025",
  "source_url": "https://example.com/guidelines",
  "last_updated": "2025-01-01",
  "procedures": [
    {
      "code": "D2542",
      "description": "Onlay - metallic - two surfaces",
      "requirements": [
        "Current dated pre-operative radiographs",
        "Prior placement date and rationale for replacement, if applicable"
      ],
      "notes": "Additional special instructions or exceptions"
    }
  ]
}
```

### 3.4 Error Handling & Logging
- Implement comprehensive logging of all scraping activities
- Create error handling for failed requests and extractions
- Document any carriers where automated extraction fails
- Provide manual extraction templates for failed cases

## 4. Development Phases

### 4.1 Phase 1: Setup & Initial Development (Day 1)
- Configure development environment with Python, Scrapy, and PDF tools
- Create base scraper architecture
- Develop and test scraper for 2-3 major carriers
- Establish data model and output format

### 4.2 Phase 2: Main Development (Day 1-2)
- Extend scraper to remaining major carriers
- Implement PDF extraction for carriers with downloadable guidelines
- Create data cleaning and standardization modules
- Begin initial data collection

### 4.3 Phase 3: Testing & Refinement (Day 2-3)
- Validate extracted data against source materials
- Refine extraction patterns for higher accuracy
- Address any carriers with extraction challenges
- Document carrier-specific notes and issues

### 4.4 Phase 4: Final Data Collection & Documentation (Day 3)
- Complete data collection from all accessible sources
- Organize and structure final data output
- Create comprehensive documentation
- Prepare data for vector database integration

## 5. Deliverables

### 5.1 Code
- Python scraper codebase with carrier-specific modules
- PDF extraction utilities
- Data cleaning and standardization scripts
- Documentation and setup instructions

### 5.2 Data
- Structured JSON files containing extracted guidelines for each carrier
- Master CSV index of all procedure codes and carriers
- Raw extracted data for verification purposes

### 5.3 Documentation
- Technical documentation for the scraper
- Carrier-specific notes and access methods
- Data dictionary explaining the structure
- Instructions for updating the scraper for future years

## 6. Risks & Considerations

### 6.1 Technical Risks
- Some carrier websites may employ anti-scraping measures
- PDF formats may vary significantly between carriers
- Some guidelines might only be available behind secured provider portals
- Rate limiting might slow down the extraction process

### 6.2 Mitigation Strategies
- Implement respectful scraping practices (delays, respecting robots.txt)
- Develop multiple extraction patterns for different PDF formats
- Have manual extraction fallbacks for secured content
- Prioritize carriers by importance to manage time constraints

### 6.3 Legal & Ethical Considerations
- Respect terms of service for carrier websites
- Implement responsible scraping practices
- Focus on publicly available provider resources
- Document sources for all extracted information

## 7. Future Enhancements

### 7.1 Potential Improvements
- Automated scheduled updates for regular guideline checks
- Email notifications for detected guideline changes
- Differential analysis between 2024 and 2025 guidelines
- Integration with Dental Narrator's vector database
- Web interface for managing carrier data

### 7.2 Maintenance Plan
- Document update process for future years
- Create test cases for verifying extraction accuracy
- Establish monitoring for carrier website changes

## 8. Conclusion
This PRD outlines a focused approach to creating a web scraper for collecting 2025 dental insurance guidelines. By following this plan, the project should successfully extract the necessary data from major carriers within the specified 2-3 day timeframe, providing the foundation for updating the Dental Narrator application with current information.