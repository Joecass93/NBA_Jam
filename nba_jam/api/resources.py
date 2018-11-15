from tastypie.resources import ModelResource
from api.models import Results, Picks, CurrWeek, Last30d, Last7d
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

class CurrWeekResource(ModelResource):
    class Meta:
        queryset = CurrWeek.objects.all()
        resource_name = 'currweek'
        authorization = Authorization()

class Last7dResource(ModelResource):
    class Meta:
        queryset = Last7d.objects.all()
        resource_name = 'last7d'
        authorization = Authorization()

class Last30dResource(ModelResource):
    class Meta:
        queryset = Last30d.objects.all()
        resource_name = 'last30d'
        authorization = Authorization()
