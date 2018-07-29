import requests
import ast
import json
import pandas as pd
from assets import range_all_dates
from config import teams, seasons
import datetime
from argparse import ArgumentParser
#from merged_data_builder import scoreboard, get_daily_stats
#from pulls import spreads_scraper

gameday = range_all_dates(start_date = '2017-10-17', end_date = '2018-04-11')
gameday_reform = []
for m in gameday:
	reformat_date = datetime.datetime.strptime(m, "%Y/%m/%d").strftime("%Y%m%d")
	gameday_reform.append(reformat_date)

print gameday
print gameday_reform
