import pytest

from services.email_parser import _parse_bg_color


@pytest.mark.parametrize("style, expected", [
    ("background:#92D050", "green"),
    ("background:#A9D08E", "green"),
    ("background:#C5E0B3", "green"),
    ("background:#FFC000", "yellow"),
    ("background:#FFE599", "yellow"),
    ("background:#FFF2CC", "yellow"),
    ("background:red", "red"),
    ("background:#FDD3D3", "red"),
    ("background:#F7CAAC", "red"),
    ("background:#D0CECE", "grey"),
    ("background:#D9D9D9", "grey"),
    ("background:#BFBFBF", "grey"),
    ("background:#DEEAF6", "blue"),
    ("background:#FFFFFF", "white"),
    ("background:black", "black"),
    ("", "unknown"),
])
def test_parse_bg_color(style, expected):
    assert _parse_bg_color(style) == expected
