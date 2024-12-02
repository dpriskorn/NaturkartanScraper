import logging
from pprint import pprint
from typing import List, Any, Dict, Set

from pydantic import BaseModel
from requests import Session

from models.municipality import Municipality

logger = logging.getLogger(__name__)


class Municipalities(BaseModel):
    municipalities: Set[Municipality] = set()
    data: List[Dict[str, Any]] = list()
    base_url: str = "https://api.naturkartan.se"
    headers: Dict[str, Any] = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Accept": "application/vnd.api+json",
        "Accept-Language": "en-US,en;q=0.5",
        # 'Accept-Encoding': 'gzip, deflate, br',
        "Referer": "https://map.naturkartan.se/",
        "Pragma": "x-hw-cache-all",
        "Cache-Control": "max-age=0",
        "Content-Type": "application/vnd.api+json",
        "X-Naturkartan-API-Key": "d6682e8c-eacb-4b79-bcb2-b0ea9686f7ae",
        "Origin": "https://map.naturkartan.se",
        "DNT": "1",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        # Requests doesn't support trailers
        # 'TE': 'trailers',
    }
    session: Session = Session()

    class Config:
        arbitrary_types_allowed = True

    def parse_data(self, response):
        for m in response.json()["data"]:
            self.data.append(m)

    def fetch_next_results(self, next_link: str = "") -> str:
        # Concatenate the base URL with the next link
        if next_link:
            url = self.base_url + next_link
        else:
            url = self.base_url + "/v3/municipalities"
        logger.info(f"downloading url: {url}")
        # Make a GET request to fetch the next results
        response = self.session.get(url, headers=self.headers)

        if response.status_code == 200:
            if not response.status_code == 200:
                raise ValueError("did not get 200")
            self.parse_data(response)
            data = response.json()
            if data.get("links") and data.get("links").get("next"):
                next = data.get("links").get("next")
                logger.info(f"found next: {next}")
                return next
        else:
            raise ValueError("did not get 200")
            # return ""  # Return None if there's an error fetching the results

    def download_all(self):
        next_link = ""
        count = 1
        while True:
            logger.info(f"request = {count}, len(data) = {len(self.data)}")
            next_link = self.fetch_next_results(next_link=next_link)
            count += 1
            # break the loop if
            if not next_link:
                break

    @staticmethod
    def preprocess_item(item):
        """clean up the mess"""
        new_item = dict()
        for key, value in item.items():
            if key == "attributes":
                attributes = item.get("attributes")
                lat = attributes.get("lat")
                lon = attributes.get("lon")
                if attributes and (lat is None or lon is None):
                    logger.debug("found none")
                    attributes["lat"] = 0.0
                    attributes["lon"] = 0.0
                new_item["attributes"] = attributes
            else:
                new_item[key] = value
        return new_item

    def parse_into_objects(self):
        for item in self.data:
            item = self.preprocess_item(item)
            pprint(item)
            instance = Municipality(**item)
            self.municipalities.add(instance)
        print(f"Found {len(self.municipalities)} unique municipalities")

    # def parse_from_file(self):
    #     try:
    #         with open("municipalities.json", "r") as file:
    #             data = json.load(file)
    #             entries = data.get("data")
    #             for hit in entries:
    #                 # processed_hit = self.preprocess_data(hit)
    #                 # pprint(processed_hit)
    #                 instance = Municipality(**hit)
    #                 # print(instance.name_sv)
    #                 # print(instance.wikidata_qid(name_sv=instance.name_sv))
    #                 self.municipalities.append(instance)
    #             print(f"Found {len(self.municipalities)} municipalities")
    #     except FileNotFoundError:
    #         print("File not found!")
    #
    def lookup_from_id(self, id_: int) -> Municipality:
        for m in self.municipalities:
            if m.id == id_:
                return m
        # raise ValueError(f"municipality with id {id_} not found")
        logger.error(f"municipality with id {id_} not found")

    def download_and_parse(self):
        self.download_all()
        self.parse_into_objects()
