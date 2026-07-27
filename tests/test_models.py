from core.models import AvailabilityStatus, Brand, ProcessingStatus


def test_enum_values():
    assert ProcessingStatus.pending.value == "pending"
    assert ProcessingStatus.completed.value == "completed"
    assert AvailabilityStatus.green.value == "green"
    assert AvailabilityStatus.red.value == "red"


def test_brand_creation():
    brand = Brand(division="Passenger", brand_category="PHC Clutch", is_active=True)
    assert brand.division == "Passenger"
    assert brand.brand_category == "PHC Clutch"
    assert brand.is_active is True
