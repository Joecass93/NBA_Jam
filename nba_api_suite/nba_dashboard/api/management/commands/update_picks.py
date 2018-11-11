import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from os.path import expanduser
import sys
home_dir = expanduser("~")
sys.path.insert(0, "%s/projects/NBA_Jam/"%home_dir)
from utilities import db_connection_manager

from django.core.management.base import BaseCommand
from api.models import Picks


class Command(BaseCommand):

    args = '<foo bar ...>'
    help = 'ayo its ya boy Joey Pickems'

    def _get_picks(self):

        self.conn = db_connection_manager.establish_db_connection('sqlalchemy').connect()

        self.results_df = pd.read_sql("SELECT * FROM results_table", con = self.conn)

        self._delete_picks()

        for index, row in self.results_df.iterrows():

            self._update_picks(row)

    def _update_picks(self, data):

        result = Picks(game_id = data['game_id'], game_date = data['game_date'],
                     away_team = data['away_team'], home_team = data['home_team'],
                     pts_away = data['pts_away'], pts_home = data['pts_home'],
                     vegas_spread_str = data['vegas_spread_str'], pred_spread_str = data['pred_spread_str'],
                     result = data['result'], id = data['game_id'])

        result.save()

    def _delete_picks(self):

        Picks.objects.all().delete()

        return None

    def handle(self, *args, **options):
        self._get_picks()
