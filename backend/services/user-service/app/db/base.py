from typing import Any
from sqlalchemy.ext.declarative import as_declarative, declared_attr

@as_declarative()
class Base:
    id: Any
    __name__: str

    # Automatically generate table names from class names
    # e.g., class User -> table 'user'
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
