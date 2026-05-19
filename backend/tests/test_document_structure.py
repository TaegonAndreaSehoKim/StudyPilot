from app.services.document_structure import build_study_context, extract_study_sections, prepare_study_text


def test_prepare_study_text_removes_repeated_headers_and_page_numbers() -> None:
    text = "\n\n".join(
        [
            "OMSCS AI Lecture Notes\n1\n# Search\nSearch explores state spaces.",
            "OMSCS AI Lecture Notes\n2\n# Planning\nPlanning uses actions.",
            "OMSCS AI Lecture Notes\n3\n# Games\nGames use adversarial search.",
        ]
    )

    prepared = prepare_study_text(text)

    assert "OMSCS AI Lecture Notes" not in prepared
    assert "\n1\n" not in prepared
    assert "Search explores state spaces" in prepared


def test_prepare_study_text_cleans_pdf_slide_artifacts() -> None:
    text = """
Page 3 of 37
Ty p e o f M o v e m e n t
A We mi g h t h a v e a g a me w i t h discrete movement.
A Specific locations are connected according to adjacency.
Relaxed de.nition uses .xed size variables and .oats.
""".strip()

    prepared = prepare_study_text(text)

    assert "Page 3 of 37" not in prepared
    assert "Type of Movement" in prepared
    assert "A We" not in prepared
    assert "might have a game" in prepared
    assert "definition" in prepared
    assert "fixed" in prepared
    assert "floats" in prepared


def test_extract_study_sections_detects_markdown_and_numbered_headings() -> None:
    text = "# Search Algorithms\nSearch explores state spaces.\n\n2. Planning\nPlanning uses actions and goals."

    sections = extract_study_sections(text)

    assert [section.title for section in sections] == ["Search Algorithms", "2. Planning"]
    assert "state spaces" in sections[0].content
    assert "actions and goals" in sections[1].content


def test_build_study_context_includes_focus_topics() -> None:
    context = build_study_context("# Search\nSearch uses heuristics.", focus_topics=["Heuristics", "Planning"])

    assert context.startswith("Review Focus Topics: Heuristics, Planning")
    assert "Section: Search" in context
