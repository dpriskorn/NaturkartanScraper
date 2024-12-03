import logging
from typing import List, Optional

from pydantic import BaseModel
from requests import Session
from wikibaseintegrator.wbi_helpers import execute_sparql_query
from bs4 import BeautifulSoup, SoupStrainer

logger = logging.getLogger(__name__)


class Trail(BaseModel):
    name_sv: str = ""
    name_en: str = ""
    id: str
    type: str
    importance: int
    popularity: int
    guide_ids: List[int]
    difficulty: Optional[str] = None
    time: int = 0 # in minutes
    trip_ids: List[int]
    category_ids: List[int]
    organization_id: int
    wheelchair_tested: bool
    # main_icon_id: int
    municipality_id: int
    average_rating: float = 0.0
    path: str
    trail_status_reported_at: Optional[str] = None
    published: bool
    imgix_url: str
    # main_category_icon: str
    length: float = 0.0 # what unit is this?
    lat: float = 0.0
    lng: float = 0.0
    publisher: str = ""
    county: str = ""

    def municipality_qid(self, municipalities) -> str:
        m = municipalities.lookup_from_id(id_=self.municipality_id)
        if m:
            return m.wikidata_qid(m.name_sv)
        else:
            raise ValueError("municipality not found")

    def municipality_name_sv(self, municipalities) -> str:
        m = municipalities.lookup_from_id(id_=self.municipality_id)
        if m:
            return m.name_sv
        else:
            raise ValueError("municipality not found")


    @property
    def qid(self) -> str:
        """Looks up QID based on the Naturkartan id property"""
        # see discussion https://www.wikidata.org/wiki/Property_talk:P10467#Include_/sv_in_the_id_and_change_name_to_path?
        path_without_prefix = self.path.replace("/sv", "")
        query = f"""
        SELECT ?item
            WHERE 
            {{
              ?item wdt:P10467 "{self.id}". 
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
        elif len(qids) == 1:
            raise ValueError("got no or more than one ")
        else:
            logger.info("trail not found in WD")
            return ""

    @property
    def url(self):
        # return f"https://www.naturkartan.se/{self.path}"
        return f"https://api.naturkartan.se/{self.id}"

    def fetch_publisher(self, session: Session):
        print("fetching publisher")

        response = session.get(self.url)
        if response.status_code == 200:
            print(self.url)
            # Parse the HTML
            soup = BeautifulSoup(response.text, 'lxml')

            # Find the <script> tag with the desired attribute
            script_tag = soup.find('script', {'event-organization': True})

            # Extract the value of the 'event-organization' attribute
            if script_tag:
                event_organization = script_tag['event-organization']
                print("Extracted Event Organization:", event_organization)
                event_county = script_tag['event-county']
                print("Extracted Event county:", event_county)
            else:
                raise ValueError("Script tag with 'event-organization' not found.")
            self.publisher = event_organization
            self.county = event_county