from services.email_parser import _detect_language, _has_arabic, _parse_bg_color


def test_parse_bg_color_green():
    assert _parse_bg_color("background:#92D050") == "green"


def test_parse_bg_color_yellow():
    assert _parse_bg_color("background:yellow") == "yellow"
    assert _parse_bg_color("background:#FFC000") == "yellow"


def test_parse_bg_color_red():
    assert _parse_bg_color("background:red") == "red"


def test_parse_bg_color_grey():
    assert _parse_bg_color("background:#D0CECE") == "grey"
    assert _parse_bg_color("background:#E7E6E6") == "grey"


def test_parse_bg_color_unknown():
    assert _parse_bg_color("") == "unknown"


def test_has_arabic_true():
    assert _has_arabic("مرحبا") is True


def test_has_arabic_false():
    assert _has_arabic("Hello") is False


def test_has_arabic_mixed():
    assert _has_arabic("مرحبا Hello") is True


def test_detect_language_en():
    assert _detect_language("Hello world", "How are you") == "en"


def test_detect_language_ar():
    assert _detect_language("مرحبا", "كيف حالك") == "ar"


def test_detect_language_mixed():
    assert _detect_language("Hello", "مرحبا") == "mixed"
