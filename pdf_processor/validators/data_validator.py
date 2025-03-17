from typing import Dict, List, Optional
import re
from loguru import logger

class DataValidator:
    """Validator for extracted CDT codes and requirements."""
    
    def __init__(self):
        self.cdt_pattern = re.compile(r'^D\d{4}$')
        self.min_requirement_length = 10  # Minimum characters for a requirement
        self.max_requirement_length = 500  # Maximum characters for a requirement
        
    def validate_cdt_code(self, code: str) -> bool:
        """Validate a CDT code format.
        
        Args:
            code: CDT code to validate
            
        Returns:
            bool: Whether the code is valid
        """
        return bool(self.cdt_pattern.match(code))
        
    def validate_requirement(self, requirement: str) -> bool:
        """Validate a requirement string.
        
        Args:
            requirement: Requirement text to validate
            
        Returns:
            bool: Whether the requirement is valid
        """
        if not requirement:
            return False
            
        # Check length
        if len(requirement) < self.min_requirement_length:
            return False
        if len(requirement) > self.max_requirement_length:
            return False
            
        # Check for common issues
        if requirement.isupper():  # Likely a header
            return False
        if requirement.count('.') > 5:  # Likely concatenated sentences
            return False
            
        return True
        
    def validate_requirements_list(self, requirements: List[str]) -> List[str]:
        """Validate and clean a list of requirements.
        
        Args:
            requirements: List of requirement strings
            
        Returns:
            List[str]: List of valid requirements
        """
        valid_reqs = []
        for req in requirements:
            if self.validate_requirement(req):
                valid_reqs.append(req)
            else:
                logger.warning(f"Invalid requirement: {req}")
                
        return valid_reqs
        
    def validate_extraction_results(self, results: Dict) -> Dict:
        """Validate complete extraction results.
        
        Args:
            results: Dictionary of extraction results
            
        Returns:
            Dict: Validation report
        """
        report = {
            'valid_codes': 0,
            'invalid_codes': 0,
            'valid_requirements': 0,
            'invalid_requirements': 0,
            'issues': []
        }
        
        if 'cdt_codes' not in results:
            report['issues'].append("No CDT codes found in results")
            return report
            
        for code, data in results['cdt_codes'].items():
            if not self.validate_cdt_code(code):
                report['invalid_codes'] += 1
                report['issues'].append(f"Invalid CDT code format: {code}")
                continue
                
            report['valid_codes'] += 1
            
            if 'requirements' not in data:
                report['issues'].append(f"No requirements found for code {code}")
                continue
                
            valid_reqs = self.validate_requirements_list(data['requirements'])
            report['valid_requirements'] += len(valid_reqs)
            report['invalid_requirements'] += len(data['requirements']) - len(valid_reqs)
            
            if not valid_reqs:
                report['issues'].append(f"No valid requirements found for code {code}")
                
        return report
        
    def get_validation_summary(self, report: Dict) -> str:
        """Generate a human-readable validation summary.
        
        Args:
            report: Validation report dictionary
            
        Returns:
            str: Summary of validation results
        """
        total_codes = report['valid_codes'] + report['invalid_codes']
        total_reqs = report['valid_requirements'] + report['invalid_requirements']
        
        summary = [
            "Validation Summary:",
            f"Total CDT Codes: {total_codes}",
            f"Valid CDT Codes: {report['valid_codes']} ({report['valid_codes']/total_codes*100:.1f}%)",
            f"Total Requirements: {total_reqs}",
            f"Valid Requirements: {report['valid_requirements']} ({report['valid_requirements']/total_reqs*100:.1f}%)",
            "\nIssues Found:"
        ]
        
        for issue in report['issues']:
            summary.append(f"- {issue}")
            
        return "\n".join(summary) 