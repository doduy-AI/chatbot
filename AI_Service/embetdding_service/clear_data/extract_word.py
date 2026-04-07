import docx

def extract_word(file_path: str) -> str:
    try:
        doc = docx.Document(file_path)
        result = []
        
        for block in iter_blocks(doc):
            if block["type"] == "paragraph":
                text = block["text"].strip()
                if text:
                    result.append(text)
            
            elif block["type"] == "table":
                result.append(table_to_markdown(block["table"]))
        
        return "\n\n".join(result)
    
    except Exception as e:
        print(f"  Lỗi đọc file word {file_path}: {e}")
        return ""


def iter_blocks(doc):
    """Duyệt đúng thứ tự paragraph và table trong file Word"""
    from docx.oxml.ns import qn
    
    for child in doc.element.body:
        if child.tag == qn("w:p"):
            para = docx.text.paragraph.Paragraph(child, doc)
            yield {"type": "paragraph", "text": para.text}
        
        elif child.tag == qn("w:tbl"):
            table = docx.table.Table(child, doc)
            yield {"type": "table", "table": table}


def table_to_markdown(table) -> str:
    """Chuyển bảng Word sang Markdown"""
    rows = []
    
    for i, row in enumerate(table.rows):
        cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
        rows.append("| " + " | ".join(cells) + " |")
        
        # Thêm dòng phân cách sau header
        if i == 0:
            rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
    
    return "\n".join(rows)