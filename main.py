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
ns.parse_hits_from_file()
ns.interate_trails()
