"""nba_jam URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from api.resources import ResultsResource, PicksResource
from api.resources import CurrWeekResource, Last30dResource, Last7dResource
from api.resources import TeamCurrWeekResource, TeamLast7dResource, TeamLast30dResource

results_resource = ResultsResource()
picks_resource = PicksResource()
currweek_resource = CurrWeekResource()
last7d_resource = Last7dResource()
last30d_resource = Last30dResource()
teamcurrweek_resource = TeamCurrWeekResource()
teamlast7d_resource = TeamLast7dResource()
teamlast30d_resource = TeamLast30dResource()


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/', include(results_resource.urls)),
    url(r'^api/', include(picks_resource.urls)),
    url(r'^api/', include(currweek_resource.urls)),
    url(r'^api/', include(last7d_resource.urls)),
    url(r'^api/', include(last30d_resource.urls)),
    url(r'^api/', include(teamcurrweek_resource.urls)),
    url(r'^api/', include(teamlast7d_resource.urls)),
    url(r'^api/', include(teamlast30d_resource.urls)),
]
