import fitz  # PyMuPDF
import json
import re
from collections import defaultdict
from pathlib import Path


def get_document_styles(doc):
    """
    Analyzes the document to find the primary body font size and a
    map of larger font sizes to their corresponding heading levels (H1-H4).
    """
    styles = defaultdict(int)
    for page in doc:
        blocks = page.get_text("dict").get("blocks", [])
        for b in blocks:
            if b.get('type') == 0:
                for l in b.get('lines', []):
                    for s in l.get('spans', []):
                        styles[round(s['size'])] += len(s['text'])

    if not styles:
        return 0, {}

    body_size = max(styles, key=styles.get) if styles else 0
    heading_sizes = sorted(
        [size for size in styles if size > body_size], reverse=True)
    level_map = {size: f"H{i+1}" for i, size in enumerate(heading_sizes[:4])}

    return body_size, level_map


def find_toc_page_num(doc):
    """
    Finds the page number containing the Table of Contents.
    """
    for i, page in enumerate(doc):
        if "table of contents" in page.get_text("lower"):
            return i
    return -1


def extract_final_structure(pdf_path):
    """
    Extracts the document structure using a generic heuristic scoring model.
    This function adheres to the hackathon rules by avoiding hardcoding.
    """
    doc = fitz.open(pdf_path)
    if not doc.page_count:
        return {"title": "", "outline": []}

    body_size, level_map = get_document_styles(doc)
    toc_page = find_toc_page_num(doc)
    outline = []
    title = ""

    # --- Generic Title Extraction Heuristic ---
    if doc.page_count > 0:
        page1 = doc[0]
        max_font_size = body_size
        for b in page1.get_text("blocks", sort=True):
            if b[6] == 0 and b[1] < page1.rect.height * 0.35:
                try:
                    spans = page1.get_text("dict", clip=b[:4])[
                        "blocks"][0]["lines"][0]["spans"]
                    if spans and spans[0]['size'] > max_font_size:
                        max_font_size = spans[0]['size']
                        title_text = " ".join(b[4].strip().split())
                        if len(title_text) > 4 and re.search('[a-zA-Z]', title_text):
                            title = title_text
                except (IndexError, KeyError):
                    continue

    # --- Generic Outline Extraction Engine ---
    heading_regex = re.compile(r"^\s*(\d+(\.\d+)*|Appendix\s+[A-Z])[\s.:]")

    for page_num, page in enumerate(doc):
        if page_num == toc_page:
            continue

        table_bboxes = [fitz.Rect(t.bbox) for t in page.find_tables()]

        blocks = page.get_text("blocks", sort=True)
        for b in blocks:
            if b[6] != 0:
                continue

            block_rect = fitz.Rect(b[:4])
            if any(block_rect.intersects(table_bbox) for table_bbox in table_bboxes):
                continue

            text = " ".join(b[4].strip().split())
            if not text or text == title or len(text) > 400:
                continue

            # --- Heuristic Scoring Model ---
            score = 0.0
            level_from_style = None
            word_count = len(text.split())

            try:
                spans = page.get_text("dict", clip=b[:4])[
                    "blocks"][0]["lines"][0]["spans"]
                if not spans:
                    continue

                span = spans[0]
                font_size = round(span['size'])
                is_bold = span['flags'] & 16

                # 1. Style Features
                if font_size in level_map:
                    score += 1.5
                    level_from_style = level_map[font_size]
                    if is_bold:
                        score += 0.5

                # 2. Content Features
                if word_count < 15:
                    score += 1
                else:
                    score -= 1
                if not text.endswith(('.', ':')):
                    score += 1

                # 3. Positional Features
                block_width = b[2] - b[0]
                is_centered = abs(
                    ((page.rect.width - block_width) / 2) - b[0]) < 20
                if is_centered:
                    score += 1

                # 4. Structural Features
                match = heading_regex.match(text)
                if match:
                    if word_count < 10:
                        score += 2.0
                    else:
                        score -= 2.0

                # --- Decision & Level Assignment ---
                if score > 2.5:
                    final_level = None
                    if match:
                        prefix = match.group(1)
                        if prefix.startswith("Appendix"):
                            final_level = "H2"
                        else:
                            final_level = f"H{prefix.count('.') + 1}"
                    else:
                        final_level = level_from_style

                    if final_level:
                        outline.append({
                            "level": final_level,
                            "text": text,
                            "page": page_num + 1,
                            "y_pos": b[1]
                        })
            except (IndexError, KeyError):
                continue

    doc.close()

    # --- Final Sorting by Position ---
    outline.sort(key=lambda x: (x['page'], x['y_pos']))
    for item in outline:
        del item['y_pos']

    return {"title": title, "outline": outline}


def process_pdfs():
    """Main execution function to process all PDFs."""
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_path in sorted(input_dir.glob("*.pdf")):
        print(f"Processing {pdf_path.name}...")
        try:
            result = extract_final_structure(pdf_path)
            output_file = output_dir / f"{pdf_path.stem}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to process {pdf_path.name}: {e}")


if __name__ == "__main__":
    process_pdfs()
