import requests
import ast
import json
import pandas as pd
from utilities.config import teams, seasons
import datetime
from argparse import ArgumentParser
from merged_data_builder import scoreboard


games = scoreboard('12/01/2017')
print games



