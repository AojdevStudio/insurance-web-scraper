"""Convert sample text file to PDF."""

from pathlib import Path
from fpdf import FPDF

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        # Set margins
        self.set_margins(20, 20, 20)
        
def create_pdf():
    """Create a PDF from the sample text file."""
    # Read the text file
    text_path = Path("sample_dental_guidelines.txt")
    if not text_path.exists():
        raise FileNotFoundError("Sample text file not found")
        
    # Create PDF object
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)
    
    # Add content
    with open(text_path, 'r') as file:
        for line in file:
            line = line.strip()
            if not line:  # Handle empty lines
                pdf.ln(5)
                continue
                
            if line.startswith('•'):
                # Replace bullet points with dashes
                line = '- ' + line[1:].strip()
                pdf.set_x(30)  # Indent bullet points
                pdf.multi_cell(0, 8, line)
            else:
                pdf.set_x(20)  # Reset to left margin
                # Make title text bold
                if "CDT Code:" in line or "Description:" in line or "Requirements:" in line:
                    pdf.set_font("Helvetica", 'B', 11)
                    pdf.multi_cell(0, 8, line)
                    pdf.set_font("Helvetica", size=11)
                else:
                    pdf.multi_cell(0, 8, line)
            
            pdf.ln(2)  # Add small space between lines
    
    # Save the PDF
    output_path = Path("sample_dental_guidelines.pdf")
    pdf.output(str(output_path))
    print(f"PDF created at {output_path}")

if __name__ == "__main__":
    create_pdf() 