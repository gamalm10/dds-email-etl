from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from core.models import Brand


def test_analytics_brand_create():
    engine = create_engine("sqlite:///:memory:")
    Brand.__table__.create(engine)
    with Session(engine) as session:
        brand = Brand(division="Passenger", brand_category="PHC Clutch")
        session.add(brand)
        session.commit()
        assert brand.id is not None
        assert brand.is_active is True
