from pydantic import BaseModel


class GeoLocation(BaseModel):
    lat: float
    lng: float
