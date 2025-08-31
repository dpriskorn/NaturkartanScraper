"""
The code was based on information fetched using this command. By substituting the coordinates it might be possible to download all trails
curl 'https://meili.naturkartan.se/indexes/Site_production/search' --compressed -X POST -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0' -H 'Accept: */*' -H 'Accept-Language: en-US,en;q=0.5' -H 'Accept-Encoding: gzip, deflate, br' -H 'Referer: https://map.naturkartan.se/' -H 'Authorization: Bearer a5e18712e1a769eb707c8eaed6b436d6570ca58816f508b0bd09605ef7e50e06' -H 'Content-Type: application/json' -H 'X-Meilisearch-Client: Meilisearch JavaScript (v0.35.0)' -H 'Origin: https://map.naturkartan.se' -H 'DNT: 1' -H 'Connection: keep-alive' -H 'Sec-Fetch-Dest: empty' -H 'Sec-Fetch-Mode: cors' -H 'Sec-Fetch-Site: same-site' -H 'TE: trailers' --data-raw '{"q":"","filter":"(category_ids=7 OR main_icon_id=7 OR category_ids=31 OR main_icon_id=31 OR category_ids=33 OR main_icon_id=33) AND published=true AND _geoBoundingBox([59.504563474600104, 20.669538535277013], [59.14483532911038, 15.44246097644313])","page":1,"hitsPerPage":1000,"attributesToRetrieve":["_geo","id","type","name_sv","name_en","path","published","importance","average_rating","length","popularity","difficulty","time","wheelchair_tested","trail_status_reported_at","imgix_url","guide_ids","municipality_id","organization_id","trip_ids","category_ids","main_category_icon","main_icon_id"]}'
"""
import csv
import json
import logging
import os
from typing import List, Any, Dict

import requests
from pydantic import BaseModel

import config
from models.municipalities import Municipalities
from models.trail import Trail

logger = logging.getLogger(__name__)


class NaturkartanScraper(BaseModel):
    """Class that helps scrape information from Naturkartan"""

    municipalities: Municipalities
    trails: List[Trail] = list()
    hits: List[Dict[str, Any]] = []

    @staticmethod
    def preprocess_data(data):
        """The API returns messy datatypes, so clean them up"""
        logger.debug("cleaning the data")
        cleaned_data = dict()
        for key, value in data["document"].items():
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
        # flatten _geo manually
        if data["document"].get("_geo") is not None:
            cleaned_data["lat"] = data["document"].get("_geo").get("lat")
            cleaned_data["lng"] = data["document"].get("_geo").get("lng")
        return cleaned_data

    @staticmethod
    def save_raw_page_json(data: dict, page: int, folder: str = "debug_pages"):
        """Save raw JSON of a downloaded page for debugging."""
        os.makedirs(folder, exist_ok=True)
        filename = os.path.join(folder, f"page_{page}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved raw page JSON to {filename}")

    def download_all_pages(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Origin': 'https://map.naturkartan.se',
            'Sec-GPC': '1',
            'Connection': 'keep-alive',
            'Referer': 'https://map.naturkartan.se/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'TE': 'trailers',
        }

        base_url = 'https://ts.naturkartan.se/collections/site:production/documents/search'
        session = requests.Session()

        page = 1
        while True:
            params = {
                'limit': 250,
                'page': page,
                'q': '',  # search text
                'query_by': 'name_sv,name_en,tags,_keywords_en',
                'filter_by': '(published:=true) && (category_ids:=33)',
                'sort_by': 'importance:asc',
                'include_fields': 'id,type,name_sv,name_en,path,published,importance,length,popularity,difficulty,time,municipality_id',
                'x-typesense-api-key': 'zD4qweZ97XrEwYgV1gXIhDNTlKe1uIuL'
            }

            response = session.get(base_url, params=params, headers=headers)
            if response.status_code != 200:
                print(f"Failed page {page}: {response.status_code}")
                break

            data = response.json()
            self.save_raw_page_json(data, page)
            found = data.get("found", 0)
            print(f"Downloading a total of {found} hits at 250 per page")
            hits = data.get("hits", [])
            if not hits:
                break  # no more results

            self.hits.extend(hits)
            print(f"Page {page}: {len(hits)} hits, total so far: {len(self.hits)}")
            page += 1
            # if page == 3:
            #     exit(0)
        print(f"Total downloaded hits: {len(self.hits)}")
        # exit(0)

    # def download_hiking_trails(self):
    #     headers = {
    #         'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0',
    #         'Accept': 'application/json, text/plain, */*',
    #         'Accept-Language': 'en-US,en;q=0.5',
    #         'Accept-Encoding': 'gzip, deflate, br, zstd',
    #         'Origin': 'https://map.naturkartan.se',
    #         'Sec-GPC': '1',
    #         'Connection': 'keep-alive',
    #         'Referer': 'https://map.naturkartan.se/',
    #         'Sec-Fetch-Dest': 'empty',
    #         'Sec-Fetch-Mode': 'cors',
    #         'Sec-Fetch-Site': 'same-site',
    #         'TE': 'trailers',
    #     }
    #
    #     base_url = 'https://ts.naturkartan.se/collections/site:production/documents/search'
    #     params = {
    #         'limit': 250,
    #         'q': '',
    #         'query_by': 'name_sv,name_en,tags,_keywords_en',
    #         'filter_by': (
    #             '(published:=true) && '
    #             '(category_ids:=33 || main_icon_id:=33) && '
    #             'marker_point:(54.0,10,54.0,26,70.0,26,70.0,10)'
    #         ),
    #         'sort_by': 'importance:asc',
    #         'include_fields': (
    #             'id,type,name_sv,name_en,path,published,importance,average_rating,length,'
    #             'popularity,difficulty,time,wheelchair_tested,trail_status_reported_at,imgix_url,'
    #             'guide_ids,county_id,municipality_id,organization_id,trip_ids,category_ids,'
    #             'main_category_icon,main_icon_id,marker_point,show_elevations,show_on_naturkartan'
    #         ),
    #         'x-typesense-api-key': 'zD4qweZ97XrEwYgV1gXIhDNTlKe1uIuL'
    #     }
    #     # headers = {
    #     #     'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0',
    #     #     'Accept': 'application/json, text/plain, */*',
    #     #     'Accept-Language': 'en-US,en;q=0.5',
    #     #     # 'Accept-Encoding': 'gzip, deflate, br, zstd',
    #     #     'Origin': 'https://map.naturkartan.se',
    #     #     'DNT': '1',
    #     #     'Connection': 'keep-alive',
    #     #     'Referer': 'https://map.naturkartan.se/',
    #     #     'Sec-Fetch-Dest': 'empty',
    #     #     'Sec-Fetch-Mode': 'cors',
    #     #     'Sec-Fetch-Site': 'same-site',
    #     #     # Requests doesn't support trailers
    #     #     # 'TE': 'trailers',
    #     # }
    #     #
    #     # # Initialize variables
    #     # base_url = 'https://ts.naturkartan.se/collections/site:production/documents/search'
    #     # params = {
    #     #     'limit': 250,
    #     #     'q': '',
    #     #     'query_by': 'name_sv,name_sv,tags,_keywords_sv',
    #     #     # 33 = hiking
    #     #     'filter_by': '(category_ids:=33 || main_icon_id:=33) && (published:=true) && marker_point:(60.614391346643174,10,60.614391346643174,26,67.1061086551916,26,67.1061086551916,10)',
    #     #     'include_fields': 'id,type,name_sv,name_sv,path,published,importance,average_rating,length,popularity,difficulty,time,wheelchair_tested,trail_status_reported_at,imgix_url,guide_ids,municipality_id,organization_id,trip_ids,category_ids,main_category_icon,main_icon_id,marker_point,show_elevations',
    #     #     'x-typesense-api-key': '63P7WG7kIjhT3xFBzZxpSbIDo8G2BXn5'
    #     # }
    #     #params['filter_by'] = '(category_ids:=33 || main_icon_id:=33) && (published:=true)'
    #     # headers = {
    #     #     'User-Agent': 'YourAppName/1.0',
    #     #     'Authorization': 'Bearer YourAuthToken'  # If authentication is required
    #     # }
    #
    #     # Fetch data for pages 1 to 7
    #     session = requests.Session()
    #
    #     for page in range(1, 9):
    #         params['page'] = page
    #         response = session.get(base_url, params=params, headers=headers
    #                                )
    #         if response.status_code == 200:
    #             data = response.json()
    #             hits = data["hits"]
    #             self.hits.extend(hits)
    #             print(f"Page {page} downloaded successfully with {len(hits)} hits. Total: {len(self.hits)} hits.")
    #         else:
    #             print(f"Failed to download page {page}: {response.status_code}")

    def parse_hits_into_trails(self):
        for hit in self.hits:
            processed_hit = self.preprocess_data(hit)
            # pprint(processed_hit)
            trail_instance = Trail(**processed_hit)
            self.trails.append(trail_instance)
        print(f"Processed {len(self.trails)} trails")

    # def iterate_trails(self):
    #     count_not_found = 0
    #     count_found = 0
    #     for trail in self.trails:
    #         #print(trail.municipality_qid(municipalities=self.municipalities))
    #         qid = trail.qid
    #         if qid:
    #             # print(f"found qid: {qid}")
    #             count_found += 1
    #         else:
    #             count_not_found += 1
    #         print(trail.name_sv)
    #         print(f"{trail.length} km")
    #         print(trail.url)
    #         print(f"{count_found} found and {count_not_found} not found out of {self.number_of_trails}")
    #         pprint(trail.model_dump())
    #         sleep(5)
    #     #print(f"{count_not_found} not found out of {self.number_of_trails}")

    @property
    def hiking_trails(self) -> List[Trail]:
        return [trail for trail in self.trails if trail.type == "Trail" and
                # no bike routes
                "cykel" not in trail.name_sv
                # exclude paths that are not really trails
                #  "stig" not in trail.name_sv)
                # we don't want a lot of short paths because they are not notable
                and config.minimum_trail_length_in_km <= trail.length < config.maximum_trail_length_in_km
                ]

    # def fetch_publishers(self):
    #     session = requests.Session()
    #     count = 1
    #     for trail in self.hiking_trails:
    #         print(f"fetching publisher {count}/{len(self.hiking_trails)} ")
    #         trail.fetch_publisher(session=session)
    #         count +=1

    def ask_user_for_information(self):
        count = 1
        for trail in self.hiking_trails:
            print(f"Working on {count}/{len(self.hiking_trails)}")
            trail.get_information(municipalities=self.municipalities, count=count, total=len(self.hiking_trails))
            count += 1

    def load_hits_from_debug_pages(self, folder: str = "debug_pages") -> None:
        """Read all hits from previously saved debug JSON pages."""
        if not os.path.exists(folder):
            logger.warning(f"Debug folder {folder} does not exist.")
            return

        for filename in sorted(os.listdir(folder)):
            if filename.endswith(".json"):
                path = os.path.join(folder, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        hits = data.get("hits", [])
                        self.hits.extend(hits)
                        logger.info(f"Loaded {len(hits)} hits from {filename}")
                except Exception as e:
                    logger.error(f"Failed to read {filename}: {e}")

        logger.info(f"Total hits loaded from debug pages: {len(self.hits)}")

    def export_trails_to_csv(self, filename: str = "trails.csv"):
        """
        Export a list of Trail objects to a CSV file.

        Args:
            filename (str): Path to the output CSV file.
        """
        # Define the header for the CSV file
        header = [
            # "qid",
            "id",
            "url",
            "name_sv",
            "name_sv + length",
            # "name_en",
            # "lat",
            # "lon",
            "municipality",
            "length",
            "length_url",
            "sections",
            "sections_url",
            "popularity"
            # "type"
            # "publisher"
        ]

        # Open the file in write mode
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)

            # Write the header row
            writer.writerow(header)

            # Write the data rows
            for trail in self.hiking_trails:
                # print(trail.model_dump())
                # exit()
                try:
                    # Use trail attributes and lookup for municipality_qid
                    row = [
                        # trail.qid,  # QID
                        trail.id,  # Trail ID
                        trail.url,
                        trail.name_sv,  # Swedish name
                        f"{trail.name_sv} {trail.length} km",  # Swedish name
                        # trail.name_en,  # English name
                        # trail.lat,  # Latitude
                        # trail.lng,  # Longitude
                        trail.municipality_name_sv(municipalities=self.municipalities),  # Municipality QID
                        trail.length,  # Length
                        trail.length_source_url,
                        trail.number_of_sections,
                        trail.section_source_url,
                        trail.popularity,
                        # trail.type  # Type
                        # trail.publisher
                    ]
                    writer.writerow(row)
                except Exception as e:
                    # Log or handle errors (e.g., missing data or failed lookups)
                    logging.error(f"Failed to export trail {trail.id}: {e}")
        print(f"Exported {len(self.hiking_trails)} hiking trails to csv that are longer than {config.minimum_trail_length_in_km} km")