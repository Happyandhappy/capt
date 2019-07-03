from django.conf.urls import url

from .views import (
    DashboardView,
    CampaignListView,
    CampaignKeywordView,
    CampaignRunsView,
    CampaignSettingsView,
)

urlpatterns = [
    url(r'^$', DashboardView.as_view(), name='reports_dashboard'),
    url(r'^campaigns/$', CampaignListView.as_view(), name='reports_campaign_list'),
    url(
        r'^campaigns/(?P<campaign_id>\d+)/$',
        CampaignKeywordView.as_view(),
        name='reports_campaign_detail',
    ),
    url(
        r'^campaigns/(?P<campaign_id>\d+)/runs/$',
        CampaignRunsView.as_view(),
        name='reports_campaign_detail_runs',
    ),
    url(
        r'^campaigns/(?P<campaign_id>\d+)/settings/$',
        CampaignSettingsView.as_view(),
        name='reports_campaign_detail_settings',
    ),
]
