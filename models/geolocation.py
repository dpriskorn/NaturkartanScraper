from pydantic import BaseModel


class GeoLocation(BaseModel):
    lat: float
    lng: float

    @property
    def latitude(self) -> float:
        return self.lat or 0.0

    @property
    def longitude(self):
        return self.lng or 0.0
