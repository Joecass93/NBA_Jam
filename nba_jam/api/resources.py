from tastypie.resources import ModelResource
from api.models import Results
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
