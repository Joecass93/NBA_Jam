import pandas as pd
from datetime import datetime, date
from django.core.management.base import BaseCommand
from api.models import Results
import sqlalchemy

class Command(BaseCommand):
    help = 'Gets the freshest results and picks'

    def handle(self, *args, **options):

        self._get_results()

    def _get_results(self):
        self.money_conn = establish_db_connection('sqlalchemy', 'moneyteam')

        self.results_df = pd.read_sql("SELECT * FROM results_table", con = self.money_conn)

        self._delete_from_model()

        for index, row in self.results_df.iterrows():
            self._update_results(row)

    def _update_results(self, data):

        result = Results(game_id = data['game_id'], game_date = data['game_date'], away_team = data['away_team'],
                         home_team = data['home_team'], away_pts = data['pts_away'], home_pts = data['pts_home'],
                         vegas_spread_str = data['vegas_spread_str'], pred_spread_str = data['pred_spread_str'],
                         pick_str = data['pick_str'], team_covered = data['team_covered'], team_picked = data['team_picked'],
                         result = data['result'], best_bet = data['best_bet'], id = data['game_id'])

        result.save()

    def _delete_from_model(self):

        Results.objects.all().delete()




def establish_db_connection(connection_package, db):

    if db == 'moneyteam':

        engine = sqlalchemy.create_engine('mysql://' + 'moneyteamadmin' + ':' + 'moneyteam2018' +
            '@' + 'nba-jam.c5tgdlkxq25p.us-east-2.rds.amazonaws.com' + ':' + '3306' + '/nba_master', encoding='utf-8')

        return engine
    elif db == 'nbaapi':

        engine = sqlalchemy.create_engine('mysql://' + 'nbajamadmin' + ':' + 'moneyteam2018' +
            '@' + 'aas6wo5k9lybv0.c5tgdlkxq25p.us-east-2.rds.amazonaws.com' + ':' + '3306' + '/nba_api', encoding='utf-8')

        return engine

    else:

        raise ValueError('Invalid connection package - ' + str(connection_package) )
