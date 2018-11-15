import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from django.core.management.base import BaseCommand
from api.models import Results, Picks, CurrWeek, Last7d, Last30d
import sqlalchemy
from utilities import establish_db_connection

class Command(BaseCommand):

    help = "builds a json containing analytics about the model's performance"

    def handle(self, *args, **options):

        self._get_data()

        self._build_date_breakdowns()

    def _get_data(self):

        self.conn = establish_db_connection('sqlalchemy', 'moneyteam')

        self.results_df = pd.read_sql("SELECT * FROM results_table", con = self.conn)


    def _build_date_breakdowns(self):

        today = datetime.now().date()
        today_str = today.strftime('%B %d, %Y')

        breakdowns = {'CurrWeek': today - timedelta(days=today.weekday() + 1),
                      'Last30d': today - timedelta(days = 31),
                      'Last7d': today - timedelta(days = 8),
                      }

        for b, f in breakdowns.iteritems():

            self._delete_from_model(b)

            sub_df = self.results_df[(self.results_df['game_date'] >= f) & (self.results_df['game_date'] < today)]

            tot_wins = len(sub_df[sub_df['result'] == 'Win'])
            tot_losses = len(sub_df[sub_df['result'] == 'Loss'])
            tot_nobets = len(sub_df[sub_df['result'] == 'No Bet'])
            tot_bestbets = len(sub_df[sub_df['best_bet'] == 'Y'])
            tot_bb_wins = len(sub_df[(sub_df['best_bet'] == 'Y') & (sub_df['result'] == 'Win')])

            _model = eval(b)
            agg_data = _model(total_games = len(sub_df), total_bestbets = tot_bestbets,
                              wins = tot_wins, losses = tot_losses,
                              no_bets = tot_nobets, best_bet_wins = tot_bb_wins,
                              date_range = '%s - %s'%(f.strftime('%B %d, %Y'), today_str))

            agg_data.save()

    def _delete_from_model(self, table):

        if table == 'CurrWeek':
            CurrWeek.objects.all().delete()
        elif table == 'Last30d':
            Last30d.objects.all().delete()
        elif table == 'Last7d':
            Last7d.objects.all().delete()
