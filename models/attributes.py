from typing import Optional

from pydantic import BaseModel

from models.name import Name


class Attributes(BaseModel):
    lat: float
    lon: float
    name: Name

    @property
    def name_sv(self) -> Optional[str]:
        return self.name.sv
