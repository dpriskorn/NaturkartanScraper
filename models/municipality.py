from functools import lru_cache
from typing import Optional

from pydantic import BaseModel
from wikibaseintegrator.wbi_helpers import execute_sparql_query

from models.attributes import Attributes


class Municipality(BaseModel):
    id: int
    attributes: Attributes
    type: str

    class Config:
        arbitrary_types_allowed = True

    def __eq__(self, other):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    @property
    def name_sv(self) -> Optional[str]:
        return self.attributes.name_sv + " kommun"

    @property
    def latitude(self) -> float:
        return self.attributes.lat

    @property
    def longitude(self) -> float:
        return self.attributes.lon

    # We use a maxsize of 300 here because there are only 290 different municipalities
    # We use a static method to be able to cache it
    @staticmethod
    @lru_cache(maxsize=300)
    def wikidata_qid(name_sv) -> str:
        # todo lookup and cache via name_sv
        query = f"""
        SELECT ?item
        WHERE 
        {{
          ?item wdt:P31 wd:Q127448. 
          ?item rdfs:label ?label.
          FILTER NOT EXISTS {{ ?item wdt:P576 [] }}
          FILTER((LANG(?label)) = "sv" && regex(?label, "{name_sv}"))
        }}
        """
        result = execute_sparql_query(query=query)
        # Extracting QIDs from the results
        qids = [
            result["item"]["value"].split("/")[-1]
            for result in result["results"]["bindings"]
        ]
        if qids and len(qids) == 1:
            return qids[0]
        else:
            raise ValueError("got no or more than one ")
