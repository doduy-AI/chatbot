import re


def chunk_by_paragraph(text: str, chunk_size=500, overlap=100) -> list[str]:
    paragraphs = re.split(r'\n{2,}', text)
    
    chunks = []
    current = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current) + len(para) <= chunk_size:
            current += "\n" + para
        else:
            if current.strip():
                chunks.append(current.strip())
            current = current[-overlap:] + "\n" + para
    
    if current.strip():
        chunks.append(current.strip())
    
    return chunks


def chunk_by_sentence(text: str, chunk_size=400, overlap=80) -> list[str]:
    sentences = re.split(r'(?<=[.!?;])\s+', text)
    
    chunks = []
    current = ""
    
    for sent in sentences:
        if len(current) + len(sent) <= chunk_size:
            current += " " + sent
        else:
            if current.strip():
                chunks.append(current.strip())
            current = current[-overlap:] + " " + sent
    
    if current.strip():
        chunks.append(current.strip())
    
    return chunks