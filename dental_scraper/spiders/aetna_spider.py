"""
Spider implementation for scraping Aetna dental insurance guidelines.
"""
from typing import Dict, Generator, Any, List, Tuple, Optional
from pathlib import Path
from datetime import datetime
import re
import json
import os
from dotenv import load_dotenv
import logging

from scrapy.http import Request, Response, FormRequest
from loguru import logger
import pdfplumber
from bs4 import BeautifulSoup
from scrapy import Spider
from scrapy.exceptions import IgnoreRequest

from ..models import CarrierGuidelines, Procedure, DataValidator
from .base_spider import BaseInsuranceSpider

# Load environment variables
load_dotenv()

# Set up logging
log_dir = os.path.join('logs', 'aetna')
os.makedirs(log_dir, exist_ok=True)
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = os.path.join(log_dir, f'spider_{timestamp}.log')

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

class AetnaSpider(Spider):
    """Spider for scraping Aetna dental insurance guidelines."""
    
    name = 'aetna'
    allowed_domains = ['aetnadental.com', 'aetna.com', 'ap5.aetna.com']
    login_url = 'https://ap5.aetna.com/siteminderagent/SmMakeCookie.ccc'
    target_url = 'https://www.aetnadental.com/professionals/secure/network-resources-programs/dental-office-guides.html'
    
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 3,
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'COOKIES_ENABLED': True,
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_TIMEOUT': 60,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429, 403],
        'HTTPERROR_ALLOW_ALL': True,
        'ROBOTSTXT_ENABLED': False,
        'LOG_LEVEL': 'DEBUG',
        'LOG_FILE': log_file,
        'REDIRECT_ENABLED': True,
        'COOKIES_DEBUG': True
    }
    
    def __init__(self, *args, **kwargs):
        """Initialize the Aetna spider."""
        super().__init__(*args, **kwargs)
        self.username = os.getenv('AETNA_USERNAME')
        self.password = os.getenv('AETNA_PASSWORD')
        self.logger.info(f"Initialized {self.name} spider")
        self.pdf_dir = os.path.join('data', 'pdfs', self.name)
        os.makedirs(self.pdf_dir, exist_ok=True)
        
    def start_requests(self):
        """Start with the login page."""
        if not self.username or not self.password:
            self.logger.error("Username and password are required")
            return
            
        self.logger.info("Starting login process")
        params = {
            'SMSESSION': 'QUERY',
            'PERSIST': '0',
            'TARGET': f'-SM-{self.target_url.replace(":", "--").replace("/", "--")}'
        }
        yield Request(
            url=f"{self.login_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}",
            callback=self.parse_login_page,
            errback=self.handle_error,
            dont_filter=True,
            meta={
                'dont_redirect': False,
                'handle_httpstatus_list': [302, 303, 307, 308],
                'request_info': {'step': 'initial_login', 'attempt': 1}
            }
        )

    def parse_login_page(self, response):
        """Parse the login page and submit credentials."""
        self.logger.info("Parsing login page")
        soup = BeautifulSoup(response.text, 'html.parser')
        form = soup.find('form')
        
        if not form:
            self.logger.error("Login form not found")
            self.logger.debug(f"Page content: {response.text[:2000]}")
            return
            
        # Get form action URL
        form_action = form.get('action', '')
        if not form_action:
            form_action = response.url
        elif not form_action.startswith('http'):
            form_action = response.urljoin(form_action)
            
        self.logger.info(f"Form action URL: {form_action}")
        
        # Get all form inputs
        formdata = {}
        for input_tag in form.find_all('input'):
            name = input_tag.get('name')
            value = input_tag.get('value', '')
            if name:
                formdata[name] = value
                if 'password' not in name.lower():  # Don't log password field
                    self.logger.debug(f"Form field: {name} = {value}")
                
        # Add credentials
        username_field = next((
            input_tag.get('name')
            for input_tag in form.find_all('input')
            if input_tag.get('type') in ['text', 'email'] or 'user' in input_tag.get('name', '').lower()
        ), 'USER')
        
        password_field = next((
            input_tag.get('name')
            for input_tag in form.find_all('input')
            if input_tag.get('type') == 'password' or 'pass' in input_tag.get('name', '').lower()
        ), 'PASSWORD')
        
        formdata[username_field] = self.username
        formdata[password_field] = self.password
        
        # Submit the form
        self.logger.info("Submitting login form")
        yield FormRequest(
            url=form_action,
            formdata=formdata,
            callback=self.after_login,
            errback=self.handle_error,
            dont_filter=True,
            meta={
                'dont_redirect': False,
                'handle_httpstatus_list': [302, 303, 307, 308],
                'request_info': {'step': 'login_submit', 'attempt': 1}
            }
        )

    def after_login(self, response):
        """Handle the post-login response and navigate to the target page."""
        self.logger.info("Processing login response")
        
        # Check if login was successful
        if 'login' in response.url.lower() or any(text in response.text.lower() for text in ['sign in', 'log in', 'login', 'invalid credentials']):
            self.logger.error("Login failed - still on login page or invalid credentials")
            self.logger.debug(f"Response URL: {response.url}")
            self.logger.debug(f"Response body: {response.text[:2000]}")
            return
            
        self.logger.info("Login successful, accessing target page")
        yield Request(
            url=self.target_url,
            callback=self.parse_guidelines,
            errback=self.handle_error,
            dont_filter=True,
            meta={
                'dont_redirect': False,
                'handle_httpstatus_list': [302, 303, 307, 308],
                'request_info': {'step': 'access_target', 'attempt': 1}
            }
        )

    def parse_guidelines(self, response):
        """Parse the dental guidelines page."""
        self.logger.info(f"Parsing guidelines page: {response.url}")
        
        # Look for PDF links
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for PDF links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text().lower()
            
            # Check if link points to a PDF
            if href.lower().endswith('.pdf') or 'pdf' in href.lower():
                if any(keyword in text.lower() or keyword in href.lower() for keyword in 
                      ['dental', 'guidelines', 'policies', 'procedures', 'coverage', 'clinical', 'bulletin']):
                    pdf_url = response.urljoin(href)
                    self.logger.info(f"Found PDF link: {pdf_url}")
                    yield Request(
                        url=pdf_url,
                        callback=self.parse_pdf,
                        errback=self.handle_error,
                        dont_filter=True
                    )

    def parse_pdf(self, response):
        """Parse a PDF file and extract dental procedures."""
        if not response.body or not response.url.endswith('.pdf'):
            self.logger.warning(f"Invalid PDF response from {response.url}")
            return

        filename = os.path.join(self.pdf_dir, f"{self.name}_guidelines_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        
        try:
            # Save PDF file
            with open(filename, 'wb') as f:
                f.write(response.body)
            
            procedures = self.extract_procedures(filename)
            if procedures:
                validator = DataValidator()
                for procedure in procedures:
                    try:
                        # Validate procedure data
                        is_valid, validated_procedure, errors = validator.validate_procedure_data(procedure)
                        if is_valid:
                            yield {
                                'carrier': 'Aetna',
                                'source_url': response.url,
                                'procedure': validated_procedure.dict(),
                                'extracted_date': datetime.now().isoformat(),
                                'file_name': os.path.basename(filename)
                            }
                        else:
                            self.logger.error(f"Invalid procedure data: {errors}")
                    except Exception as e:
                        self.logger.error(f"Error processing procedure: {str(e)}")
            else:
                self.logger.warning(f"No procedures extracted from {os.path.basename(filename)}")
        except Exception as e:
            self.logger.error(f"Error processing PDF {response.url}: {str(e)}")
        finally:
            # Clean up the temporary file
            if os.path.exists(filename):
                os.remove(filename)

    def extract_procedures(self, pdf_path: str) -> List[Dict]:
        """Extract dental procedures from a PDF file."""
        procedures = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # First pass: collect all text to analyze document structure
                full_text = ""
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += f"\n--- Page {page.page_number} ---\n{text}"

                # Look for sections that might contain procedures
                sections = re.split(r'\n(?=(?:SECTION|CATEGORY|PROCEDURES|GUIDELINES|POLICY)\s+[IVX0-9]+[.:)])', full_text)
                
                for section in sections:
                    # Skip empty sections
                    if not section.strip():
                        continue
                        
                    # Look for procedure codes with various formats
                    code_patterns = [
                        r'D\d{4}(?=\s|$|\)|\]|\.)',  # Standard CDT code
                        r'(?<=Code\s)D\d{4}',        # Code prefixed
                        r'(?<=CDT\s)D\d{4}',         # CDT prefixed
                        r'(?<=procedure\s)D\d{4}'    # Procedure prefixed
                    ]
                    
                    for pattern in code_patterns:
                        matches = re.finditer(pattern, section, re.IGNORECASE)
                        for match in matches:
                            code = match.group()
                            pos = match.start()
                            
                            # Get context (up to 1000 characters around the code)
                            start = max(0, pos - 500)
                            end = min(len(section), pos + 500)
                            context = section[start:end]
                            
                            # Extract description using multiple patterns
                            description = None
                            desc_patterns = [
                                rf'{code}\s*[-:]+\s*([^.]*\.)',
                                rf'{code}\s+([^.]*\.)',
                                rf'{code}\s*\(([^)]*)\)',
                                rf'{code}\s*\[([^\]]*)\]'
                            ]
                            
                            for desc_pattern in desc_patterns:
                                desc_match = re.search(desc_pattern, context, re.IGNORECASE)
                                if desc_match:
                                    description = desc_match.group(1).strip()
                                    break
                            
                            if not description:
                                continue
                            
                            # Extract requirements
                            requirements = []
                            req_indicators = [
                                'required', 'must', 'should', 'need', 'necessary',
                                'documentation', 'criteria', 'prerequisite',
                                'condition', 'requirement'
                            ]
                            
                            # Look for requirements in the context
                            for indicator in req_indicators:
                                req_matches = re.finditer(
                                    rf'({indicator}[^.;]*[.;])',
                                    context,
                                    re.IGNORECASE
                                )
                                for req_match in req_matches:
                                    req = req_match.group(1).strip()
                                    if req not in requirements:
                                        requirements.append(req)
                            
                            # Extract limitations
                            limitations = []
                            limit_indicators = [
                                'limit', 'maximum', 'minimum', 'restricted',
                                'not covered', 'excluded', 'only when',
                                'frequency', 'interval'
                            ]
                            
                            # Look for limitations in the context
                            for indicator in limit_indicators:
                                limit_matches = re.finditer(
                                    rf'({indicator}[^.;]*[.;])',
                                    context,
                                    re.IGNORECASE
                                )
                                for limit_match in limit_matches:
                                    limit = limit_match.group(1).strip()
                                    if limit not in limitations:
                                        limitations.append(limit)
                            
                            # Create the procedure object
                            procedure = {
                                'code': code,
                                'description': description,
                                'requirements': requirements or ['No specific requirements listed'],
                                'limitations': limitations or ['No specific limitations listed'],
                                'source_page': int(re.search(r'Page (\d+)', section).group(1))
                                if re.search(r'Page (\d+)', section) else 1
                            }
                            
                            # Add the procedure if it's not a duplicate
                            if not any(p['code'] == code for p in procedures):
                                procedures.append(procedure)
                                self.logger.info(f"Extracted procedure {code}")
                            
        except Exception as e:
            self.logger.error(f"Error extracting procedures from PDF: {str(e)}")
        
        if procedures:
            self.logger.info(f"Extracted {len(procedures)} procedures from {pdf_path}")
        else:
            self.logger.warning(f"No procedures found in {pdf_path}")
            
        return procedures

    def handle_error(self, failure):
        """Handle request errors."""
        request_info = failure.request.meta.get('request_info', {})
        step = request_info.get('step', 'unknown')
        attempt = request_info.get('attempt', 1)
        
        self.logger.error(f"Request failed during step '{step}' (attempt {attempt}): {failure.value}")
        if hasattr(failure.value, 'response'):
            response = failure.value.response
            self.logger.error(f"Response status: {response.status}")
            self.logger.error(f"Response headers: {response.headers}")
            self.logger.error(f"Response body: {response.text[:2000]}")  # Log first 2000 chars
        
        # If we haven't exceeded max retries and it's a retryable error
        if attempt < 3 and hasattr(failure.value, 'response'):
            response = failure.value.response
            if response.status in [429, 500, 502, 503, 504]:
                self.logger.info(f"Retrying request (attempt {attempt + 1})")
                return Request(
                    url=failure.request.url,
                    callback=failure.request.callback,
                    errback=self.handle_error,
                    dont_filter=True,
                    meta={
                        'dont_redirect': False,
                        'handle_httpstatus_list': [302, 303, 307, 308],
                        'request_info': {'step': step, 'attempt': attempt + 1}
                    }
                )
        
        return None 