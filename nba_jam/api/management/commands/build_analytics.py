import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from django.core.management.base import BaseCommand
from api.models import Results, Picks, CurrWeek, Last7d, Last30d
from api.models import TeamsLast30d, TeamsLast7d, TeamsCurrWeek
import sqlalchemy
from utilities import establish_db_connection, list_games, teams

class Command(BaseCommand):

    help = "builds jsons containing analytics about the model's performance"

    def handle(self, *args, **options):

        self.conn = establish_db_connection('sqlalchemy', 'moneyteam')

        self.today = datetime.now().date()
        self.today_str = self.today.strftime('%B %d, %Y')

        self.breakdowns = {'CurrWeek': self.today - timedelta(days=self.today.weekday() + 1),
                           'Last30d': self.today - timedelta(days = 31),
                           'Last7d': self.today - timedelta(days = 8),
                            }
        self.team_breakdowns = {}
        for i, j in self.breakdowns.iteritems():
            self.team_breakdowns['Teams%s'%i] = j

        self._build_date_breakdowns()
        self._build_team_breakdowns()

    def _build_date_breakdowns(self):

        data = pd.read_sql("SELECT * FROM results_table", con = self.conn)

        for b, f in self.breakdowns.iteritems():
            delete_from_model(b)

            sub_df = data[(data['game_date'] >= f) & (data['game_date'] < self.today)]

            tot_wins = len(sub_df[sub_df['result'] == 'Win'])
            tot_losses = len(sub_df[sub_df['result'] == 'Loss'])
            tot_nobets = len(sub_df[sub_df['result'] == 'No Bet'])
            tot_bestbets = len(sub_df[sub_df['best_bet'] == 'Y'])
            tot_bb_wins = len(sub_df[(sub_df['best_bet'] == 'Y') & (sub_df['result'] == 'Win')])

            _model = eval(b)
            agg_data = _model(total_games = len(sub_df), total_bestbets = tot_bestbets,
                              wins = tot_wins, losses = tot_losses,
                              no_bets = tot_nobets, best_bet_wins = tot_bb_wins,
                              date_range = '%s - %s'%(f.strftime('%B %d, %Y'), self.today_str))

            agg_data.save()

    def _build_team_breakdowns(self):

        ## delete current data from api
        for tbl, dts in self.team_breakdowns.iteritems():
            delete_from_model(tbl)

        ## get dict of teams and game ids played
        games_dict = {}
        for i, t in teams.iteritems():
            games_dict[i] = list_games(i, self.today.strftime("%Y-%m-%d"))

        for team, games in games_dict.iteritems():
            team_dict = {}
            team_df_str = "SELECT * FROM results_table WHERE game_id IN ('%s')"%("', '".join(games))
            team_df = pd.read_sql(team_df_str, con = self.conn)

            for b, f in self.team_breakdowns.iteritems():
                sub_team_df = team_df[(team_df['game_date'] >= f) & (team_df['game_date'] < self.today)]
                start_date = sub_team_df['game_date'].min().strftime('%B %d, %Y')
                end_date = sub_team_df['game_date'].max().strftime('%B %d, %Y')

                _team_model = eval(b)
                team_agg_data = _team_model(team = teams.get(team), team_id = team,
                                           games = len(sub_team_df),
                                           wins = len(team_df[(team_df['result'] == 'Win') & (team_df['team_picked'] == teams.get(team))]),
                                           games_picked = len(team_df[(team_df['result'] != 'No Bet') & (team_df['team_picked'] == teams.get(team))]),
                                           losses = len(team_df[(team_df['result'] == 'Loss') & (team_df['team_picked'] == teams.get(team))]),
                                           total_bb_picked = len(team_df[(team_df['best_bet'] == 'Y') & (team_df['team_picked'] == teams.get(team))]),
                                           best_bet_wins = len(team_df[(team_df['best_bet'] == 'Y') & (team_df['result'] == 'Win')]),
                                           date_range = "%s - %s"%(start_date, end_date),
                                           fav_games = 0,
                                           cover_games = len(team_df[team_df['team_covered'] == teams.get(team)]),
                                           team_abbrv = "")
                team_agg_data.save()




def delete_from_model(table):

    model = eval(table)
    model.objects.all().delete()

    # if table == 'CurrWeek':
    #     CurrWeek.objects.all().delete()
    # elif table == 'Last30d':
    #     Last30d.objects.all().delete()
    # elif table == 'Last7d':
    #     Last7d.objects.all().delete()
    # el
