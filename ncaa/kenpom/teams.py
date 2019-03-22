import pyrebase
import firebase_admin
from firebase_admin import credentials
import pandas as pd
from nba_utilities.db_connection_manager import establish_db_connection
from os.path import expanduser

### fetch teams
conn = establish_db_connection('sqlalchemy').connect()
teams = pd.read_sql('SELECT DISTINCT Team FROM kenpom_four_factors_data', con=conn)
teams = [ t.strip() for t in teams['Team'] ]

### push to firebase
path = "%s/Documents/knockout_creds.json"%expanduser("~")
config = {
    'apiKey': "AIzaSyDEhRpfi82QXYfDqo8L0Y54SLUUuTp7Vk0",
    'authDomain': "ncaa-knockout-2019.firebaseapp.com",
    'databaseURL': "https://ncaa-knockout-2019.firebaseio.com",
    'projectId': "ncaa-knockout-2019",
    'storageBucket': "ncaa-knockout-2019.appspot.com",
    'messagingSenderId': "104831088386",
    'serviceAccount':path
  }

firebase = pyrebase.initialize_app(config)
db = firebase.database()

for t in teams:
    db.child('teams').push({'team': t})
