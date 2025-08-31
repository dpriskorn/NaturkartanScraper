import logging

from wikibaseintegrator.wbi_config import config as wbconfig

import config
from models.municipalities import Municipalities
from models.naturkartan_scraper import NaturkartanScraper

wbconfig["USER_AGENT"] = config.user_agent

logging.basicConfig(level=config.loglevel)
logger = logging.getLogger(__name__)

m = Municipalities()
m.download_and_parse()
ns = NaturkartanScraper(municipalities=m)
#ns.download_hiking_trails()
#ns.download_all_pages()
ns.load_hits_from_debug_pages()
ns.parse_hits_into_trails()
# ns.ask_user_for_information()
ns.export_trails_to_csv()
# ns.interate_trails()
