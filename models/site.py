import logging

import requests
from bs4 import SoupStrainer, BeautifulSoup
from pydantic import BaseModel
from requests import Session
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.datatypes import ExternalID
from wikibaseintegrator.wbi_enums import ActionIfExists

logger = logging.getLogger(__name__)

class Site(BaseModel):
    qid: str
    path: str
    base_url: str = "https://www.naturkartan.se/sv/"
    session: Session = Session()
    html: str = ""
    id: int = 0
    wbi: WikibaseIntegrator

    class Config:
        arbitrary_types_allowed = True

    @property
    def needs_migration(self):
        """If the path is already numeric, it is already migrated"""
        return not self.path.isnumeric()

    @property
    def url(self):
        return self.base_url + self.path


    def download_html(self):
        try:
            response = self.session.get(self.url)
            if response.status_code == 200:
                self.html = response.text
            else:
                print(f"Failed to fetch HTML. Status code: {response.status_code}")
        except requests.RequestException as e:
            print(f"Request Exception: {e}")
        return None

    def find_new_id(self):
        """search using bs4 for data-naturkartan-preselected-site-id
        <div class="site-page-media__map"><div class="map-new" data-site-page-target="map" data-naturkartan-app-base="" data-naturkartan-api-base="https://api.naturkartan.se" data-naturkartan-naturkartan-base="https://www.naturkartan.se" data-naturkartan-meili-env="production" data-naturkartan-language="sv" data-naturkartan-disable-autoload="true" data-naturkartan-menu="fullscreen" data-naturkartan-query="site_with_neighbours=13979" data-naturkartan-strict="site" data-naturkartan-preselected-site-id="13979" data-controller="map-new" data-map-new-script-value="https://map-embed.naturkartan.se/embed.js"></div>
        """
        # Create a SoupStrainer to parse only the 'div' elements with class 'map-new'
        only_map_new_div = SoupStrainer("div", class_="map-new")

        # Parse the HTML using the SoupStrainer
        soup = BeautifulSoup(self.html, 'lxml', parse_only=only_map_new_div)

        # Find the 'div' element with class 'map-new' and extract the value of 'data-naturkartan-preselected-site-id'
        div_element = soup.find('div', class_='map-new')
        if div_element:
            preselected_site_id = div_element.get('data-naturkartan-preselected-site-id')
            if preselected_site_id is not None:
                print("Preselected Site ID:", preselected_site_id)
                self.id = int(preselected_site_id)
            else:
                logger.error("found no site id")
        else:
            print("No 'map-new' div found.")

    def migrate_to_new_id(self):
        if self.id:
            item = self.wbi.item.get(self.qid)
            item.claims.remove(property="P10467")
            # pprint(item.get_json())
            # exit()
            claim = ExternalID(
                prop_nr="P10467",
                value=str(self.id)
            )
            item.add_claims(claims=[claim], action_if_exists=ActionIfExists.REPLACE_ALL)
            # pprint(item.get_json())
            # input("press enter to continue")
            item.write(summary="Migrated to new ID using [[Wikidata:Tools/NaturkartanScraper|NaturkartanScraper]]")
            # print(item.get_entity_url())
            print("Upload complete")
            # input("press enter to continue")

    @property
    def wikidata_url(self):
        return f"https://www.wikidata.org/wiki/{self.qid}"