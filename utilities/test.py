import requests
import ast
import json
import pandas as pd
from utilities.config import teams, seasons
import datetime
from argparse import ArgumentParser
from merged_data_builder import scoreboard, get_daily_stats
from pulls import spreads_scraper

dates = ['12/01/2017', '12/02/2017']
for i, x in enumerate(dates):
	games = scoreboard(x)
	if i == 0:
		final = games
		print final
	else:
		print games
		final = final.append(games)
		print final

daily_data = get_daily_stats(final)
#spreads = spreads_scraper.main()

print daily_data
print final

