from app.services.chunking import chunk_text


def test_chunk_text_long_input() -> None:
    text = "\n\n".join(f"Paragraph {index} " + ("x" * 120) for index in range(30))

    chunks = chunk_text(text, max_chars=500, overlap_chars=50)

    assert len(chunks) > 1
    assert all(chunk.strip() for chunk in chunks)
    assert all(len(chunk) <= 650 for chunk in chunks)
