from tastypie.resources import ModelResource
from api.models import Results, Picks
from tastypie.authorization import Authorization

class ResultsResource(ModelResource):
    class Meta:
        queryset = Results.objects.all()
        resource_name = 'results'
        authorization = Authorization()
        filtering = {
            "game_date":'exact',
            "home_team":'exact',
            "away_team":'exact',
            "result":'exact',
            "best_bet":'exact',
            "team_picked":'exact',
            "team_covered":'exact'
        }

class PicksResource(ModelResource):
    class Meta:
        queryset = Picks.objects.all()
        resource_name = 'picks'
        authorization = Authorization()
        filtering = {
            "home_team":'exact',
            "away_team":'exact',
            "best_bet":'exact'
        }
