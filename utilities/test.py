import requests
import ast
import json
import pandas as pd
from utilities.config import teams, seasons
import datetime
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-s", "--start_season", help="season to start pulling final scores data from: ex. 2000-01", type=str, required=False)
parser.add_argument("-e", "--end_season", help = "season to end pulling final scores data from: ex. 2000-01", type=str, required=False)

flags = parser.parse_args()

if flags.start_season:
	first = flags.start_season
else:
	first = '2000-01'

if flags.end_season:
	second = flags.end_season
else:
	second = '2017-18'

print first
print second

