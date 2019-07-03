from django.conf.urls import url

from .views import (
    AdwordsPreambleView,
    CompatibilityResultsView,
    PaymentFailedView,
    ProceedToPaymentGatewayView,
    QuoteEstimateView,
    QuoteView,
)


urlpatterns = [
    url(
        r'^welcome/$',
        AdwordsPreambleView.as_view(),
        name='quoting_adwords_preamble',
    ),
    url(
        r'^quote-estimate/$',
        QuoteEstimateView.as_view(),
        name='quoting_quote_estimate',
    ),
    url(
        r'^quote/$',
        QuoteView.as_view(),
        name='quoting_view_quote',
    ),
    url(
        r'^compatibility-results/$',
        CompatibilityResultsView.as_view(),
        name='quoting_compatibility_results',
    ),
    url(
        r'^proceed-to-payment-gateway/$',
        ProceedToPaymentGatewayView.as_view(),
        name='quoting_proceed_to_payment_gateway',
    ),
    url(
        r'^card-verification-failed/$',
        PaymentFailedView.as_view(),
        name='quoting_payment_failed',
    ),
]
