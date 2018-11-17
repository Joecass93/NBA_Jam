from tastypie.resources import ModelResource
from api.models import Results, Picks, CurrWeek, Last30d, Last7d
from api.models import TeamsCurrWeek, TeamsLast30d, TeamsLast7d
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

class TeamCurrWeekResource(ModelResource):
    class Meta:
        queryset = TeamsCurrWeek.objects.all()
        resource_name = 'teamcurrweek'
        authorization = Authorization()
        filtering = {
            "team":'exact',
            "team_id":'exact'
        }

class TeamLast7dResource(ModelResource):
    class Meta:
        queryset = TeamsLast7d.objects.all()
        resource_name = 'teamlast7d'
        authorization = Authorization()
        filtering = {
            "team":'exact',
            "team_id":'exact'
        }

class TeamLast30dResource(ModelResource):
    class Meta:
        queryset = TeamsLast30d.objects.all()
        resource_name = 'teamlast30d'
        authorization = Authorization()
        filtering = {
            "team":'exact',
            "team":'exact'
        }
