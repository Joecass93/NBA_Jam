import requests
import ast
import json
import pandas as pd
from utilities.config import teams, seasons
import datetime
from argparse import ArgumentParser
from merged_data_builder import scoreboard, get_daily_stats
from pulls import spreads_scraper


games = scoreboard('12/01/2017')
#daily_data = get_daily_stats(games)
#spreads = spreads_scraper.main()

print games
print list(games)

