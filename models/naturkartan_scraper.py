"""
The code was based on information fetched using this command. By substituting the coordinates it might be possible to download all trails
curl 'https://meili.naturkartan.se/indexes/Site_production/search' --compressed -X POST -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://map.naturkartan.se/' -H 'Authorization: Bearer a5e18712e1a769eb707c8eaed6b436d6570ca58816f508b0bd09605ef7e50e06' -H 'Content-Type: application/json' -H 'X-Meilisearch-Client: Meilisearch JavaScript (v0.35.0)' -H 'Origin: https://map.naturkartan.se' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-site' -H 'TE: trailers' --data-raw '{"q":"","filter":"(category_ids=7 OR main_icon_id=7 OR category_ids=31 OR main_icon_id=31 OR category_ids=33 OR main_icon_id=33) AND published=true AND _geoBoundingBox([59.504563474600104, 20.669538535277013], [59.14483532911038, 15.44246097644313])","page":1,"hitsPerPage":1000,"attributesToRetrieve":["_geo","id","type","name_sv","name_en","path","published","importance","average_rating","length","popularity","difficulty","time","wheelchair_tested","trail_status_reported_at","imgix_url","guide_ids","municipality_id","organization_id","trip_ids","category_ids","main_category_icon","main_icon_id"]}'
"""
import json
import logging
from pprint import pprint
from typing import List

from pydantic import BaseModel

from models.municipalities import Municipalities
from time import sleep

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
            qid = trail.qid
            if qid:
                # print(f"found qid: {qid}")
                count_found += 1
            else:
                count_not_found += 1
            print(trail.name_sv)
            print(f"{trail.length} km")
            print(trail.url)
            print(f"{count_found} found and {count_not_found} not found out of {self.number_of_trails}")
            pprint(trail.model_dump())
            sleep(5)
        #print(f"{count_not_found} not found out of {self.number_of_trails}")

    @property
    def number_of_trails(self) -> int:
        return len(self.trails)