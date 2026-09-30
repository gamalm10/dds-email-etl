from services.chat_service import CHUNK_DELAY_SECONDS, chunk_for_streaming


def test_chunk_empty_returns_empty_list():
    assert chunk_for_streaming("") == []
    assert chunk_for_streaming("   ") == []


def test_chunk_short_text_stays_single_chunk():
    assert chunk_for_streaming("PHC Clutch is in transit.") == ["PHC Clutch is in transit."]


def test_chunk_splits_on_sentences():
    text = (
        "The answer is green. "
        "PHC Clutch ships on 22.08 and is on track. "
        "No further delays are expected."
    )
    chunks = chunk_for_streaming(text)
    assert len(chunks) > 1
    assert "".join(chunks) == text


def test_chunk_preserves_all_content():
    text = "First part here. Second part follows. Third and final part."
    assert "".join(chunk_for_streaming(text)) == text


def test_chunk_splits_on_newlines():
    # Short text stays whole because it is below the minimum chunk size.
    assert chunk_for_streaming("Line one\nLine two\nLine three") == [
        "Line one\nLine two\nLine three"
    ]

    text = (
        "Evidence section header that is reasonably long here\n"
        "- first bullet point with some detail\n"
        "- second bullet point with more detail to follow\n"
        "Insights section header that is also long enough here\n"
        "- third bullet point carrying additional context\n"
    )
    chunks = chunk_for_streaming(text)
    assert len(chunks) >= 2
    assert "".join(chunks) == text.strip()


def test_chunk_keeps_bullet_lists_intact():
    text = (
        "Direct answer: several brands are at risk.\n\n"
        "Evidence:\n- PHC Clutch is delayed\n- A-part Clutches is red\n\n"
        "Insights:\n- Supply chain instability is increasing\n"
    )
    chunks = chunk_for_streaming(text)
    assert "".join(chunks) == text.strip()
    assert any("\n" in c for c in chunks)


def test_chunk_handles_no_sentence_punctuation():
    text = "a" * 200
    chunks = chunk_for_streaming(text)
    assert "".join(chunks) == text


def test_chunk_long_unpunctuated_single_chunk():
    text = "word " * 100
    chunks = chunk_for_streaming(text)
    assert "".join(chunks) == text.strip()


def test_chunk_delay_is_short_enough_to_feel_streamed():
    assert 0 < CHUNK_DELAY_SECONDS <= 0.2


def test_chunk_preserves_markdown_headings():
    text = (
        "**Direct answer:**\nThe portfolio is stable.\n\n"
        "**Insights:**\nThere is an information gap on eight brands."
    )
    assert "".join(chunk_for_streaming(text)) == text.strip()


def test_chunk_strips_only_outer_whitespace():
    text = "\n\n  Answer starts here. And continues.  \n\n"
    chunks = chunk_for_streaming(text)
    assert "".join(chunks) == text.strip()
