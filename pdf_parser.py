import sys
import json
import pdfplumber

def is_word_in_table(word, tables):
    """
    Check if a word's bounding box overlaps with any table's bounding box.
    """
    w_x0, w_top, w_x1, w_bottom = word['x0'], word['top'], word['x1'], word['bottom']
    for t in tables:
        t_x0, t_top, t_x1, t_bottom = t.bbox
        # Check overlap (with 1 unit of tolerance)
        if not (w_x1 < t_x0 + 1 or w_x0 > t_x1 - 1 or w_bottom < t_top + 1 or w_top > t_bottom - 1):
            return True
    return False

def extract_pdf_data(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            if not pdf.pages:
                print(json.dumps({"error": "PDF has no pages"}, indent=2))
                return
            
            # Target the first page
            page = pdf.pages[0]
            
            # 1. Locate and extract tables
            tables = page.find_tables()
            
            # 2. Extract all words from the page
            all_words = page.extract_words()
            
            # 3. Filter out words that lie inside any table area to isolate normal text
            non_table_words = [w for w in all_words if not is_word_in_table(w, tables)]
            
            # 4. Group remaining words into lines
            # Sort words by top position, then left-to-right (x0)
            non_table_words.sort(key=lambda w: (w['top'], w['x0']))
            
            lines = []
            if non_table_words:
                current_line = [non_table_words[0]]
                for w in non_table_words[1:]:
                    # If vertical distance is small, group in same line
                    if abs(w['top'] - current_line[-1]['top']) < 3:
                        current_line.append(w)
                    else:
                        current_line.sort(key=lambda x: x['x0'])
                        lines.append(current_line)
                        current_line = [w]
                current_line.sort(key=lambda x: x['x0'])
                lines.append(current_line)
            
            # 5. Group lines into paragraphs/blocks based on vertical distance
            blocks = []
            current_block = []
            prev_bottom = None
            
            for line in lines:
                line_text = " ".join([w['text'] for w in line]).strip()
                if not line_text:
                    continue
                
                line_top = min(w['top'] for w in line)
                line_bottom = max(w['bottom'] for w in line)
                
                if prev_bottom is None:
                    current_block.append((line_text, line_top, line_bottom))
                else:
                    # If vertical gap is relatively large (more than 10 units), start new block
                    gap = line_top - prev_bottom
                    if gap > 10:
                        blocks.append(current_block)
                        current_block = [(line_text, line_top, line_bottom)]
                    else:
                        current_block.append((line_text, line_top, line_bottom))
                prev_bottom = line_bottom
                
            if current_block:
                blocks.append(current_block)
                
            # 6. Format text blocks
            formatted_blocks = []
            for block in blocks:
                text = "\n".join([line[0] for line in block])
                top = block[0][1]
                bottom = block[-1][2]
                formatted_blocks.append({
                    "type": "text",
                    "text": text,
                    "top": top,
                    "bottom": bottom
                })
                
            # 7. Format tables with their bounding boxes
            formatted_tables = []
            for t in tables:
                formatted_tables.append({
                    "type": "table",
                    "data": t.extract(),
                    "top": t.bbox[1],
                    "bottom": t.bbox[3]
                })
                
            # 8. Merge both lists and sort vertically (top-to-bottom)
            all_elements = sorted(formatted_blocks + formatted_tables, key=lambda x: x['top'])
            
            # 9. Structure final output and associate tables with the last seen text block (header/context)
            structured_content = []
            last_text = "Header/Context not found"
            
            for el in all_elements:
                if el['type'] == 'text':
                    structured_content.append({
                        "type": "text",
                        "content": el['text']
                    })
                    # Keep the last text block as prospective context for the next table
                    last_text = el['text']
                elif el['type'] == 'table':
                    structured_content.append({
                        "type": "table",
                        "associated_context": last_text,
                        "data": el['data']
                    })
            
            # Output JSON structured results
            print(json.dumps(structured_content, indent=2))
            
    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_parser.py <path_to_pdf>")
        sys.exit(1)
    extract_pdf_data(sys.argv[1])
