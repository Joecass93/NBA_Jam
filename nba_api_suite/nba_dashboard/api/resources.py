from tastypie.resources import ModelResource
from api.models import Picks


class PicksResource(ModelResource):
    class Meta:
        queryset = Picks.objects.all()
        resource_name = 'picks'
