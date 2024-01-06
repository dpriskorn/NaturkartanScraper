import json
import logging
from typing import List

from pydantic import BaseModel

from models.municipalities import Municipalities
from models.trail import Trail

logger = logging.getLogger(__name__)


class NaturkartanScraper(BaseModel):
    """Class that helps scrape information from Naturkartan"""

    municipalities: Municipalities
    trails: List[Trail] = list()

    @staticmethod
    def preprocess_data(data):
        """The API returns messy datatypes, so clean them up"""
        logger.debug("cleaning the data")
        cleaned_data = dict()
        for key, value in data.items():
            if key == "name_en" and (value == "" or value is None or value == "None"):
                cleaned_data[key] = ""
            elif (key == "time" or key == "length" or key == "municipality_id") and (
                value == "" or value is None or value == "None"
            ):
                cleaned_data[key] = 0
            elif key == "average_rating" and (
                value == "" or value is None or value == "None"
            ):
                logger.debug("cleaning up average_rating")
                cleaned_data[key] = 0.0
            elif key == "length" and isinstance(value, str):
                cleaned_data[key] = float(value)
            else:
                cleaned_data[key] = value
        return cleaned_data

    def parse_hits_from_file(self):
        try:
            with open("hits.json", "r") as file:
                data = json.load(file)
                hits = data.get("hits")
                for hit in hits:
                    processed_hit = self.preprocess_data(hit)
                    # pprint(processed_hit)
                    trail_instance = Trail(**processed_hit)
                    self.trails.append(trail_instance)
                print(f"Found {len(self.trails)} trails to process")
        except FileNotFoundError:
            print("File not found!")

    def interate_trails(self):
        count_not_found = 0
        count_found = 0
        for trail in self.trails:
            #print(trail.municipality_qid(municipalities=self.municipalities))
            #pprint(trail.model_dump())
            qid = trail.qid
            if qid:
                # print(f"found qid: {qid}")
                count_found += 1
            else:
                count_not_found += 1
            print(f"{count_found} found and {count_not_found} not found out of {self.number_of_trails}")
            # pprint(trail.model_dump())
            # exit()
        #print(f"{count_not_found} not found out of {self.number_of_trails}")

    @property
    def number_of_trails(self) -> int:
        return len(self.trails)