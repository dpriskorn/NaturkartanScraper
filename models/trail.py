import logging
import re
import webbrowser
from typing import List, Optional

from bs4 import BeautifulSoup
from consolemenu import SelectionMenu
from pydantic import BaseModel
from requests import Session
from wikibaseintegrator.wbi_helpers import execute_sparql_query

logger = logging.getLogger(__name__)


class Trail(BaseModel):
    name_sv: str = ""
    name_en: str = ""
    id: str
    type: str
    importance: int
    popularity: int
    guide_ids: List[int] = []
    difficulty: Optional[str] = None
    time: int = 0 # in minutes
    trip_ids: List[int] = []
    category_ids: List[int] = []
    organization_id: int = 0
    wheelchair_tested: bool = False
    # main_icon_id: int
    municipality_id: int = 0
    average_rating: float = 0.0
    path: str
    trail_status_reported_at: Optional[str] = None
    published: bool
    imgix_url: str = ""
    # main_category_icon: str
    length: float = 0.0 # what unit is this?
    lat: float = 0.0
    lng: float = 0.0
    publisher: str = ""
    county: str = ""
    number_of_sections: int = 0
    length_source_url: str = ""
    section_source_url: str = ""
    already_in_wikidata: bool = False
    wikidata: str = ""

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

    @staticmethod
    def ask_url(
        text: str,
    ):
        """Ask mandatory question"""
        answer = input(
            f"{text}: [mandatory]:",
        )
        if len(answer) > 0:
            return answer

    @staticmethod
    def ask_int(
        text: str = "Input number of sections:",
    ):
        answer = input(
            f"{text}: [km]:",
        )
        if len(answer) > 0:
            return int(answer)
        else:
            return 0

    @staticmethod
    def ask_float(
        text: str = "Input length:",
    ):
        answer = input(
            f"{text}: [km]:",
        )
        if len(answer) > 0:
            return float(answer.replace(",", "."))
        else:
            return 0.0

    def get_information(self, municipalities, count: int, total: int):
        if not municipalities:
            raise ValueError()
        municipality = self.municipality_name_sv(municipalities=municipalities)
        print(f"Trail: {self.name_sv} in {municipality}")
        self.find_in_wikidata(municipality=municipality, count=count, total=total)
        if not self.already_in_wikidata:
            print(f"Trail: {self.name_sv} in {municipality}")
            print("Opening google to search")
            webbrowser.open(f"https://www.google.com/search?q={self.name_sv}+{municipality}")
            self.get_length_and_source_url()
            self.get_section_and_source_url()
            # pprint(self.model_dump())
            # exit()

    def get_length_and_source_url(self):
        self.length = self.ask_float()
        self.length_source_url = self.ask_url(text="Please paste a source url which state the length of the path")

    def get_section_and_source_url(self):
        self.number_of_sections = self.ask_int()
        self.section_source_url = self.ask_url(text="Please paste a source url which "
                                                          "state the number of sections of the path")

    def find_in_wikidata(self, municipality=None, count=0, total=0):
        print("Opening wikidata to search")
        webbrowser.open(f"https://www.wikidata.org/w/index.php?search={self.name_sv}&title=Special%3ASearch&ns0=1")
        # A SelectionMenu constructs a menu from a list of strings
        selection_menu = SelectionMenu(title=f"Is {self.name_sv} in {municipality} "
                                             f"already in Wikidata? "
                                             f"({count}/{total})", strings=["Yes", "No"])
        selection_menu.show()
        if selection_menu.selected_option == 0:
            self.already_in_wikidata = True
        print(selection_menu.selected_option)
        # we default to false so no else is needed

    @property
    def clean_name_sv(self) ->str:
        # reverse when there is a comma
        parts = self.name_sv.split(",")
        if len(parts) == 2:
            # reverse
            name = f"{parts[1].strip()} {parts[0].strip()}"
        else:
            # ignore more parts than 3
            name = ",".join(parts)

        # replace
        clean_1 = (name
                .replace(" - En del av Smålandsleden","")
                # .replace(",","")
                .replace("-", " – ")  # dash with spaces
                .replace("  "," ")  # collapse spaces
                .replace("<>","–")
                # .replace("","")
        )
        clean_2 = re.sub(r"\b\d{2} km\b", "", clean_1) # \b is word boundary
        return clean_2
