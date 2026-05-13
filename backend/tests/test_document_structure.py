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
