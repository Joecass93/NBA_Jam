from draft_kings import Sport, Client
from datetime import datetime, date
import pandas as pd
import pulp

class LinearOptimization:

    def __init__(self):
        self.today = datetime.now().date()

    def _determine_player_pool(self):

        contests = Client().contests(sport=Sport.NBA)

        # for contest in contests.contests:
        #     print( contest )
        #     print()
        #     if contest.payout == 350000:
        #         main_contest = contest
        draft_groups = []
        for contest in contests.contests:
            draft_groups.append(contest.draft_group_id)

        ## remove dupes from draft group list
        draft_groups = list(set(draft_groups))
        print( draft_groups )


        player_pool = Client().available_players(draft_group_id=main_contest.draft_group_id)

        players = []
        for player in player_pool.players:
            if player.draft_details.is_draftable is True:
                player_info = {
                    "fname": player.first_name,
                    "lname": player.last_name,
                    "player_id": player.player_id,
                    "position": player.position_details.name,
                    "position_id": player.position_details.position_id,
                    "salary": player.draft_details.salary,
                    "team_id": player.team_id,
                    "ppg": player.points_per_game

                }
                players.append(player_info)


        self.df = pd.DataFrame(players)

        print( self.df )

    def _position_data(self):
        pass

    def _build_algo(self):
        prob = pulp.LpProblem('NBA', pulp.LpMaximize)



def main():
    algo = LinearOptimization()

    algo._determine_player_pool()
    # algo._build_algo()

if __name__ == "__main__":
    main()
