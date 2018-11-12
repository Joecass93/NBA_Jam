from tastypie.resources import ModelResource
from api.models import Results
from tastypie.authorization import Authorization

class ResultsResource(ModelResource):
    class Meta:
        queryset = Results.objects.all()
        resource_name = 'results'
        authorization = Authorization()
