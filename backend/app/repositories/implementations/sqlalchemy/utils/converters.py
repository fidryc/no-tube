from sqlalchemy.orm import DeclarativeBase

def to_dict(model: DeclarativeBase) -> dict:
    return {c.name: getattr(model, c.name) for c in model.__table__.columns}