"""
Data cleaning utilities for dental insurance guidelines.

This module contains functions and classes for cleaning and standardizing data
extracted from dental insurance PDFs.
"""

import re
import datetime
from typing import Dict, List, Optional, Any, Union
from loguru import logger

from dental_scraper.exceptions import DataCleaningException


class TextNormalizer:
    """
    Utility class for normalizing text.
    """
    
    def __init__(self):
        """Initialize the text normalizer."""
        self.rules = {
            'spacing': r'\s+',
            'bullets': r'[•●■◆★]',
            'quotes': r'[""'']',
            'dashes': r'[‒–—―]'
        }
    
    def normalize(self, text: str) -> str:
        """
        Normalize text by removing extra whitespace and standardizing formatting.
        
        Args:
            text (str): The text to normalize
            
        Returns:
            str: The normalized text
        """
        if not text:
            return ""
        
        # Replace unicode with ASCII
        text = self._replace_unicode(text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Trim whitespace
        text = text.strip()
        
        return text
    
    def _replace_unicode(self, text: str) -> str:
        """
        Replace unicode characters with ASCII equivalents.
        
        Args:
            text (str): The text to process
            
        Returns:
            str: The processed text
        """
        if not text:
            return ""
        
        # Replace bullets
        text = re.sub(self.rules['bullets'], '*', text)
        
        # Replace quotes
        text = re.sub(self.rules['quotes'], '"', text)
        
        # Replace dashes
        text = re.sub(self.rules['dashes'], '-', text)
        
        return text


class CDTCodeCleaner:
    """
    Utility class for cleaning and validating CDT codes.
    """
    
    def __init__(self):
        """Initialize the CDT code cleaner."""
        self.pattern = r'^D\d{4}$'
    
    def clean(self, code: str) -> str:
        """
        Clean and standardize a CDT code.
        
        Args:
            code (str): The CDT code to clean
            
        Returns:
            str: The cleaned CDT code
        """
        if not code:
            return ""
        
        # Remove whitespace
        code = code.strip()
        
        # If already in correct format, return as is
        if re.match(self.pattern, code):
            return code.upper()
        
        # Try to fix common issues
        # Remove any non-alphanumeric characters
        code = re.sub(r'[^a-zA-Z0-9]', '', code)
        
        # Ensure 'D' is uppercase
        if code.lower().startswith('d'):
            code = 'D' + code[1:]
        
        # Check if code is valid after cleaning
        if re.match(self.pattern, code):
            return code
        
        logger.warning(f"Could not clean CDT code: {code}")
        return ""
    
    def validate(self, code: str) -> bool:
        """
        Validate if a CDT code is properly formatted.
        
        Args:
            code (str): The CDT code to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not code:
            return False
        
        return bool(re.match(self.pattern, code))


class RequirementsCleaner:
    """
    Utility class for cleaning and standardizing procedure requirements.
    """
    
    def __init__(self):
        """Initialize the requirements cleaner."""
        self.bullet_pattern = r'^[\s•\-\*]+\s*'
    
    def clean(self, requirements: List[str]) -> List[str]:
        """
        Clean and standardize a list of requirements.
        
        Args:
            requirements (list): The list of requirements to clean
            
        Returns:
            list: The cleaned requirements
        """
        if not requirements:
            return []
        
        # Clean each requirement
        cleaned_requirements = []
        for req in requirements:
            if not req:
                continue
            
            # Normalize text
            req = req.strip()
            
            # Remove bullet points and other markers
            req = re.sub(self.bullet_pattern, '', req)
            
            # Skip empty requirements
            if not req:
                continue
            
            cleaned_requirements.append(req)
        
        # Remove duplicates while preserving order
        unique_requirements = []
        for req in cleaned_requirements:
            if req not in unique_requirements:
                unique_requirements.append(req)
        
        return unique_requirements


class DateNormalizer:
    """
    Utility class for normalizing dates.
    """
    
    def __init__(self):
        """Initialize the date normalizer."""
        self.date_formats = [
            '%m/%d/%Y',
            '%Y-%m-%d',
            '%b %d, %Y',
            '%d-%b-%Y'
        ]
    
    def normalize(self, date_str: str) -> str:
        """
        Normalize a date string to ISO format (YYYY-MM-DD).
        
        Args:
            date_str (str): The date string to normalize
            
        Returns:
            str: The normalized date string in ISO format
        """
        if not date_str:
            return ""
        
        date_str = date_str.strip()
        
        # Try different date formats
        for fmt in self.date_formats:
            try:
                date_obj = datetime.datetime.strptime(date_str, fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        logger.warning(f"Could not normalize date: {date_str}")
        return date_str


class DataValidator:
    """
    Utility class for validating structured data.
    """
    
    def __init__(self):
        """Initialize the data validator."""
        self.code_cleaner = CDTCodeCleaner()
    
    def validate_structure(self, data: Dict) -> Dict:
        """
        Validate the structure of data.
        
        Args:
            data (dict): The data to validate
            
        Returns:
            dict: Validation results with errors
        """
        errors = {}
        
        # Check required fields for procedures
        if 'procedures' in data:
            proc_errors = []
            for i, proc in enumerate(data['procedures']):
                proc_error = {}
                
                # Check required fields
                for field in ['code', 'description', 'requirements']:
                    if field not in proc or not proc[field]:
                        proc_error[field] = f"Missing required field: {field}"
                
                if proc_error:
                    proc_errors.append({f"procedure_{i}": proc_error})
            
            if proc_errors:
                errors['procedures'] = proc_errors
        
        return errors
    
    def validate_content(self, data: Dict) -> Dict:
        """
        Validate the content of data against business rules.
        
        Args:
            data (dict): The data to validate
            
        Returns:
            dict: Validation results with errors
        """
        errors = {}
        
        # Validate procedure codes
        if 'procedures' in data:
            proc_errors = []
            for i, proc in enumerate(data['procedures']):
                proc_error = {}
                
                # Validate CDT code format
                if 'code' in proc and proc['code']:
                    if not self.code_cleaner.validate(proc['code']):
                        proc_error['code'] = f"Invalid CDT code format: {proc['code']}"
                
                # Validate requirements
                if 'requirements' in proc and not proc['requirements']:
                    proc_error['requirements'] = "Empty requirements list"
                
                if proc_error:
                    proc_errors.append({f"procedure_{i}": proc_error})
            
            if proc_errors:
                errors['procedures'] = proc_errors
        
        return errors


class DataCleaner:
    """
    Utility class for cleaning and standardizing data extracted from dental insurance PDFs.
    """
    
    def __init__(self):
        """Initialize the data cleaner."""
        logger.info("Initializing enhanced DataCleaner")
        self.text_normalizer = TextNormalizer()
        self.cdt_code_cleaner = CDTCodeCleaner()
        self.requirements_cleaner = RequirementsCleaner()
        self.date_normalizer = DateNormalizer()
        self.validator = DataValidator()
    
    def clean_text(self, text: str) -> str:
        """
        Clean text by removing extra whitespace and standardizing formatting.
        
        Args:
            text (str): The text to clean
            
        Returns:
            str: The cleaned text
        """
        return self.text_normalizer.normalize(text)
    
    def clean_cdt_code(self, code: str) -> str:
        """
        Clean and standardize a CDT code.
        
        Args:
            code (str): The CDT code to clean
            
        Returns:
            str: The cleaned CDT code
        """
        return self.cdt_code_cleaner.clean(code)
    
    def clean_description(self, description: str) -> str:
        """
        Clean a procedure description.
        
        Args:
            description (str): The procedure description to clean
            
        Returns:
            str: The cleaned description
        """
        return self.text_normalizer.normalize(description)
    
    def standardize_requirements(self, requirements: List[str]) -> List[str]:
        """
        Standardize a list of requirements.
        
        Args:
            requirements (list): The list of requirements to standardize
            
        Returns:
            list: The standardized requirements
        """
        return self.requirements_cleaner.clean(requirements)
    
    def normalize_date(self, date_str: str) -> str:
        """
        Normalize a date string to ISO format.
        
        Args:
            date_str (str): The date string to normalize
            
        Returns:
            str: The normalized date string
        """
        return self.date_normalizer.normalize(date_str)
    
    def clean_procedure(self, procedure: Dict) -> Dict:
        """
        Clean a procedure dictionary.
        
        Args:
            procedure (dict): The procedure dictionary to clean
            
        Returns:
            dict: The cleaned procedure
        """
        if not procedure:
            return {}
        
        cleaned_procedure = {}
        
        # Clean code
        if 'code' in procedure:
            cleaned_procedure['code'] = self.clean_cdt_code(procedure['code'])
        
        # Clean description
        if 'description' in procedure:
            cleaned_procedure['description'] = self.clean_description(procedure['description'])
        
        # Clean requirements
        if 'requirements' in procedure:
            cleaned_procedure['requirements'] = self.standardize_requirements(procedure['requirements'])
        
        # Clean effective date
        if 'effective_date' in procedure:
            cleaned_procedure['effective_date'] = self.normalize_date(procedure['effective_date'])
        
        # Clean notes
        if 'notes' in procedure:
            cleaned_procedure['notes'] = self.clean_text(procedure['notes'])
        
        # Copy any other fields
        for key, value in procedure.items():
            if key not in cleaned_procedure:
                cleaned_procedure[key] = value
        
        return cleaned_procedure
    
    def clean_procedures(self, procedures: List[Dict]) -> List[Dict]:
        """
        Clean a list of procedures.
        
        Args:
            procedures (list): The list of procedures to clean
            
        Returns:
            list: The cleaned procedures
        """
        if not procedures:
            return []
        
        logger.info(f"Cleaning {len(procedures)} procedures")
        return [self.clean_procedure(proc) for proc in procedures]


class DataCleaningPipeline:
    """
    Pipeline for cleaning and validating data.
    """
    
    def __init__(self):
        """Initialize the data cleaning pipeline."""
        logger.info("Initializing DataCleaningPipeline")
        self.cleaner = DataCleaner()
        self.validator = DataValidator()
    
    def process(self, data: Dict) -> Dict:
        """
        Process data through the cleaning pipeline.
        
        Args:
            data (dict): The data to process
            
        Returns:
            dict: The cleaned and validated data
        """
        try:
            # Step 1: Clean the data
            cleaned_data = self._clean_data(data)
            
            # Step 2: Validate the data
            validation_errors = self._validate_data(cleaned_data)
            
            # Step 3: Handle validation errors
            if validation_errors:
                logger.warning(f"Validation errors: {validation_errors}")
                cleaned_data['validation_errors'] = validation_errors
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error in data cleaning pipeline: {str(e)}")
            raise DataCleaningException(f"Data cleaning failed: {str(e)}")
    
    def _clean_data(self, data: Dict) -> Dict:
        """
        Clean the data.
        
        Args:
            data (dict): The data to clean
            
        Returns:
            dict: The cleaned data
        """
        cleaned_data = data.copy()
        
        # Clean carrier name
        if 'carrier' in cleaned_data:
            cleaned_data['carrier'] = self.cleaner.clean_text(cleaned_data['carrier'])
        
        # Clean procedures
        if 'procedures' in cleaned_data:
            cleaned_data['procedures'] = self.cleaner.clean_procedures(cleaned_data['procedures'])
        
        # Clean dates
        if 'last_updated' in cleaned_data:
            cleaned_data['last_updated'] = self.cleaner.normalize_date(cleaned_data['last_updated'])
        
        return cleaned_data
    
    def _validate_data(self, data: Dict) -> Dict:
        """
        Validate the data.
        
        Args:
            data (dict): The data to validate
            
        Returns:
            dict: Validation errors
        """
        structure_errors = self.validator.validate_structure(data)
        content_errors = self.validator.validate_content(data)
        
        # Merge errors
        all_errors = {}
        
        if structure_errors:
            all_errors['structure'] = structure_errors
            
        if content_errors:
            all_errors['content'] = content_errors
            
        return all_errors 