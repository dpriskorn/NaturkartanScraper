from typing import Optional

from pydantic import BaseModel


class Name(BaseModel):
    id: Optional[str]
    nl: Optional[str]
    de: Optional[str]
    en: Optional[str]
    fi: Optional[str]
    pl: Optional[str]
    sv: Optional[str]
