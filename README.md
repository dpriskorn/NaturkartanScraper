# Naturkartan Scraper
This tool was build to quickly enrich the hiking trails in Wikidata by scraping from Naturkartan.

As of december 2024 a total of 1566 trails are found.

# Features
* downloads and preprocesses all hiking trails from Naturkartan and export to csv

## Deprecated
* Migrated ids from strings to integers

# License
GPLv3+

# What I learned writing this
* flattening json is a good design pattern as a standard when consuming apis with nested objects
* I got a little more experience with a JSON API and handling nexturl in a while loop