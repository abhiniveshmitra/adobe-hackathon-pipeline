import pdfplumber
import os
import json
import re
from collections import Counter

# --- Configuration ---
INPUT_DIR = "input_pdfs"
OUTPUT_DIR = "output_outlines"
OUTPUT_FILENAME = "structured_output.json"

def is_likely_heading(line, common_font_size):
    """
    Heuristic to determine if a line is a heading.
    - It has a larger font size than the most common text.
    - It's short and doesn't end with a period.
    """
    if not line['chars']:
        return False
    
    line_font_size = line['chars'][0]['size']
    line_text = line['text'].strip()
    
    # A heading is typically larger than the body text and relatively short.
    return (line_font_size > common_font_size + 1) and (len(line_text.split()) < 10)

def is_list_item(line_text):
    """
    Identifies if a line of text is a list item using regex.
    Matches common bullet points (•, *, -) or numbered patterns (1., a., etc.).
    """
    list_pattern = re.compile(r'^\s*([•*-]|\d+\.|\w\.)\s+')
    return bool(list_pattern.match(line_text))

def process_pdf(pdf_path):
    """
    Processes a single PDF to extract its content and a detailed structure.
    This version uses advanced heuristics for better element identification.

    Args:
        pdf_path (str): The full path to the PDF file.

    Returns:
        dict: A dictionary containing the hierarchically structured content of the PDF.
    """
    document_structure = {
        "pdf_path": os.path.basename(pdf_path),
        "pages": []
    }

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_elements = []
            
            # --- Advanced Text and Structure Analysis ---
            words = page.extract_words(x_tolerance=2, y_tolerance=2, keep_blank_chars=True, use_vertical_lines=True, extra_attrs=['size', 'fontname'])
            
            # Find the most common font size to differentiate body text from headings
            if words:
                font_sizes = [round(word['size'], 2) for word in words]
                # Use the most common font size as the baseline for paragraph text
                most_common_size = Counter(font_sizes).most_common(1)[0][0] if font_sizes else 10
            else:
                most_common_size = 10 # Default size if no words found

            # Extract text lines with detailed character info
            lines = page.extract_text_lines(layout=True, strip=False, return_chars=True)
            
            for line in lines:
                line_text = line['text'].strip()
                if not line_text:
                    continue
                
                element_type = "paragraph" # Default type
                if is_likely_heading(line, most_common_size):
                    element_type = "heading"
                elif is_list_item(line_text):
                    element_type = "list_item"

                page_elements.append({
                    "type": element_type,
                    "content": line_text,
                    "bbox": [line['x0'], line['top'], line['x1'], line['bottom']]
                })

            # --- Extract Tables with Advanced Settings ---
            # These settings help pdfplumber find tables more reliably
            table_settings = {
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "snap_tolerance": 3,
                "join_tolerance": 3,
            }
            tables = page.extract_tables(table_settings)
            for table_data in tables:
                page_elements.append({
                    "type": "table",
                    "content": table_data,
                    "bbox": page.bbox # Bbox for the whole page as table bbox isn't direct
                })
                
            # --- Extract Images ---
            for img in page.images:
                page_elements.append({
                    "type": "image",
                    "bbox": [img['x0'], page.height - img['y1'], img['x1'], page.height - img['y0']]
                })
            
            # Sort all elements by their vertical position on the page
            page_elements.sort(key=lambda x: x['bbox'][1])

            document_structure["pages"].append({
                "page_number": i + 1,
                "dimensions": [page.width, page.height],
                "elements": page_elements
            })

    return document_structure


if __name__ == "__main__":
    # Ensure output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    all_results = []
    
    pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    
    print(f"--- Service 1a: Document Extraction ---")
    print(f"Found {len(pdf_files)} PDF(s) to process in '{INPUT_DIR}/'.")

    for filename in pdf_files:
        try:
            pdf_path = os.path.join(INPUT_DIR, filename)
            print(f"Processing: {pdf_path}")
            
            structured_data = process_pdf(pdf_path)
            all_results.append(structured_data)
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # Write all structured data to a single JSON file
    output_filepath = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    with open(output_filepath, "w") as f:
        json.dump(all_results, f, indent=4)
        
    print(f"\n✅ Processing complete. Structured output saved to: {output_filepath}")
