from typing import List

from pydantic import BaseModel
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbconfig
from wikibaseintegrator.wbi_helpers import execute_sparql_query
from wikibaseintegrator.wbi_login import Login

import config
from models.site import Site

wbconfig["USER_AGENT"] = config.user_agent


class NaturkartanMigrator(BaseModel):
    """migrates old path based ids to new int based"""

    query: str = """
    #Cats
    SELECT ?item ?path
    WHERE 
    {
      ?item wdt:P10467 ?path.
    }
    """
    # yields 1085 results
    sites: List[Site] = list()

    def iterate_sites(self):
        number_sites = len(self.sites)
        print(f"iterating {number_sites} sites")
        count = 1
        for site in self.sites:
            print(f"working on {count}/{number_sites}")
            if site.needs_migration:
                print(site.url)
                print(site.wikidata_url)
                site.download_html()
                site.find_new_id()
                site.migrate_to_new_id()
                #from time import sleep
                #sleep(3)
                # if count % 10 == 0:
                #     input("press enter to continue")
            else:
                print("already migrated")
            count += 1

    def get_data(self) -> None:
        result = execute_sparql_query(query=self.query)
        wbi = WikibaseIntegrator(
            login=Login(user=config.user_name, password=config.bot_password)
        )
        # Extracting QIDs from the results
        self.sites = [
            Site(wbi=wbi, qid=result["item"]["value"].split("/")[-1], path=result["path"]["value"])
            for result in result["results"]["bindings"]
        ]

    def start(self):
        self.get_data()
        self.iterate_sites()


