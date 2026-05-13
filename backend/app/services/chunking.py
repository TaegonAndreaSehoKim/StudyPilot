def chunk_text(text: str, max_chars: int = 6000, overlap_chars: int = 500) -> list[str]:
    clean_text = text.strip()
    if not clean_text:
        return []
    if len(clean_text) <= max_chars:
        return [clean_text]

    paragraphs = [part.strip() for part in clean_text.split("\n\n") if part.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        if len(paragraph) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            start = 0
            while start < len(paragraph):
                end = min(start + max_chars, len(paragraph))
                piece = paragraph[start:end].strip()
                if piece:
                    chunks.append(piece)
                if end == len(paragraph):
                    break
                start = max(end - overlap_chars, start + 1)
            continue

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_chars:
            current = candidate
        else:
            chunks.append(current.strip())
            overlap = current[-overlap_chars:].strip() if overlap_chars > 0 else ""
            current = f"{overlap}\n\n{paragraph}".strip() if overlap else paragraph

    if current.strip():
        chunks.append(current.strip())

    return [chunk for chunk in chunks if chunk]
