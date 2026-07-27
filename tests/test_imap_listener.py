import pytest

from services.imap_listener import DDS_SUBJECT_PATTERN


@pytest.mark.parametrize("subject, expected", [
    ("DDS-06.07.2026", True),
    ("DDS-06.07.2026 (draft)", True),
    ("Fw: DDS-27.07.2026", True),
    ("Meeting notes", False),
    ("DDS-2026-07-06", False),
    ("RE: Operation DDS -27 July 2026", False),
    ("DDS-01.01.2027", True),
])
def test_dds_subject_pattern(subject, expected):
    assert bool(DDS_SUBJECT_PATTERN.search(subject)) == expected
