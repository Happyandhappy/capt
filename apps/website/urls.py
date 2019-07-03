from django.conf.urls import url

from .views import DismissBannerView, TermsAndConditionsView


urlpatterns = [
    url(r'^ajax/dismiss-banner/$', DismissBannerView.as_view(), name='website_dismiss_banner'),
    url(
        r'^terms-and-conditions/$',
        TermsAndConditionsView.as_view(),
        name='website_terms_and_conditions',
    ),
]
