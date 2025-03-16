"""
PDF processing utilities.

This module contains functions to extract text from PDF files and convert it to JSON.
"""

import os
import json
import PyPDF2
from pathlib import Path


def extract_text_with_pypdf2(pdf_path):
    """
    Extract text from a PDF file using PyPDF2.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        dict: Dictionary containing the extracted text with page numbers as keys
    """
    result = {}
    
    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)
        num_pages = len(reader.pages)
        
        for page_num in range(num_pages):
            page = reader.pages[page_num]
            text = page.extract_text()
            result[f"page_{page_num + 1}"] = text
    
    return result


def extract_text_with_pdfplumber(pdf_path):
    """
    Extract text from a PDF file using pdfplumber.
    
    This function requires the pdfplumber package to be installed.
    It generally provides better text extraction than PyPDF2 for complex layouts.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        dict: Dictionary containing the extracted text with page numbers as keys
    """
    import pdfplumber
    
    result = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            result[f"page_{page_num + 1}"] = text
    
    return result


def pdf_to_json(pdf_path, output_path=None, method="pypdf2"):
    """
    Convert a PDF file to a JSON file.
    
    Args:
        pdf_path (str): Path to the PDF file
        output_path (str, optional): Path to save the JSON file. If None,
                                     saves to data/json directory with same filename
        method (str, optional): Method to use for text extraction. 
                               Either "pypdf2" or "pdfplumber"
    
    Returns:
        str: Path to the saved JSON file
    """
    # Extract text based on the chosen method
    if method.lower() == "pypdf2":
        extracted_data = extract_text_with_pypdf2(pdf_path)
    elif method.lower() == "pdfplumber":
        extracted_data = extract_text_with_pdfplumber(pdf_path)
    else:
        raise ValueError("Method must be either 'pypdf2' or 'pdfplumber'")
    
    # Add metadata to the extracted data
    pdf_filename = os.path.basename(pdf_path)
    result = {
        "filename": pdf_filename,
        "source_path": pdf_path,
        "extraction_method": method,
        "content": extracted_data
    }
    
    # Determine output path
    if output_path is None:
        # Convert PDF filename to JSON filename
        json_filename = Path(pdf_filename).stem + ".json"
        # Create path in the data/json directory
        output_path = os.path.join(os.getcwd(), "data", "json", json_filename)
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write to JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4, ensure_ascii=False)
    
    return output_path


def batch_process_pdfs(pdf_directory, output_directory=None, method="pypdf2"):
    """
    Process all PDF files in a directory.
    
    Args:
        pdf_directory (str): Directory containing PDF files
        output_directory (str, optional): Directory to save JSON files
        method (str, optional): Method to use for text extraction
    
    Returns:
        list: Paths to all processed JSON files
    """
    if output_directory is None:
        output_directory = os.path.join(os.getcwd(), "data", "json")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)
    
    processed_files = []
    
    # Process each PDF file
    for filename in os.listdir(pdf_directory):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(pdf_directory, filename)
            json_filename = Path(filename).stem + ".json"
            output_path = os.path.join(output_directory, json_filename)
            
            processed_path = pdf_to_json(pdf_path, output_path, method)
            processed_files.append(processed_path)
    
    return processed_files


if __name__ == "__main__":
    # Example usage
    pdf_dir = os.path.join(os.getcwd(), "data", "pdfs")
    json_dir = os.path.join(os.getcwd(), "data", "json")
    
    # Check if there are any PDFs in the directory
    if any(f.lower().endswith(".pdf") for f in os.listdir(pdf_dir)):
        print(f"Processing PDFs in {pdf_dir}")
        processed = batch_process_pdfs(pdf_dir, json_dir)
        print(f"Processed {len(processed)} PDF files")
    else:
        print(f"No PDF files found in {pdf_dir}")
        print("Please run the spider first to download some PDFs")
