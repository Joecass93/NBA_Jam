from urllib2 import urlopen
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import csv
import os
import glob
from xlsxwriter.workbook import Workbook
import openpyxl as xl
from openpyxl import load_workbook
from datetime import datetime
from collections import OrderedDict

#Formatting dates for file naming etc..
curr_date = time.strftime("%m_%d_%y")
curr_date_reformat = time.strftime("%Y%m%d")

curr_date_reformat = '20171201'
##User defined functions
#Remove user defined prefix from a string
def remove_prefix(text, prefix):
   if text.startswith(prefix):
       return text[len(prefix):]
   #else
   return text
#Remove user defined suiffx from a string
def remove_suffix(text, suffix):
   if text.endswith(suffix):
       return text[:len(text)-len(suffix)]
   #else
   return text


###START OF SPREADS SCRAPE
#url being scrape
url = "http://www.sportsline.com/nba/odds/"
#html from the url
html = urlopen(url)

soup = BeautifulSoup(html, "html.parser")
#Scrape today's matchups
matchups = []
for a in soup.find_all('a', href=re.compile("/nba/game-forecast/NBA_" + curr_date_reformat)):
   if a.text:
       matchups.append(a['href'])

matchups_no_dupes = list(set(matchups))

#Navigate to each games landing page (in order to get each spread)
homepage = "https://sportsline.com"
landing_pages = [homepage + l for l in matchups_no_dupes]

df = pd.DataFrame()
headers = ('away', 'OvUnTag', 'OvUn', 'hometag', 'home', 'spread')
info =[]
for x in landing_pages:
   html = urlopen(x)
   soup = BeautifulSoup(html, "html.parser")
   game_info = [soup.find('div',{"class":"header-title"})]
   game_clean = [x.text for x in game_info]
   game_final = [remove_prefix(x, "\nGAME FORECAST\n") for x in game_clean]
   game_final = [remove_suffix(x, "\n")for x in game_final]
   for x in game_final:
       x = str(x)
       x = x.split(" ")
       info.append(x)
df = pd.DataFrame(info, columns=headers)
print(df)