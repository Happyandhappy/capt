from django.http import Http404, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.views.generic import CreateView, DetailView, FormView, TemplateView

from ecom6.views import PaymentDetailBaseView

from accounts.views import UnpaidAccountRequiredMixin
from adwords.adapter import Adapter

from .forms import TermsAndConditionsForm, QuoteEstimateForm
from .models import (
    CompatibilityCheckECommerceTracking,
    CompatibilityCheckOnPagePhoneCallTracking,
    CompatibilityCheckWebsiteTracking,
    Quote,
)


class AdwordsPreambleView(UnpaidAccountRequiredMixin, FormView):
    template_name = 'quotes/adwords_preamble.html'
    form_class = TermsAndConditionsForm
    success_url = reverse_lazy('accounts_oauth_redirect')


class QuoteEstimateView(UnpaidAccountRequiredMixin, CreateView):
    template_name = 'quotes/quote_estimate_form.html'
    form_class = QuoteEstimateForm

    class Meta:
        model = Quote

    def get_success_url(self):
        return reverse('quoting_view_quote')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.set_user_details(self.request.user)
        self.request.session['quote_pk'] = self.object.pk
        return HttpResponseRedirect(self.get_success_url())


class CompatibilityResultsView(UnpaidAccountRequiredMixin, TemplateView):
    template_name = 'quotes/compatibility_results.html'

    def test_func(self):
        return super().test_func() and self.request.user.has_adwords_account

    def get(self, request, *args, **kwargs):
        adapter = Adapter(self.request.user)        
        monthly_spend = adapter.get_monthly_spend()
        
        quote = Quote(monthly_adwords_spend=monthly_spend)        
        quote.set_user_details(request.user, commit=False)
        quote.calculate_quote(commit=False)
        quote.set_type_automatic(commit=False)
        quote.save()
        
        request.session['quote_pk'] = quote.pk
        
        return super().get(request, *args, **kwargs)

    def get_checks(self):
        adwords_adapter = Adapter(self.request.user)
        return [
            check_class(adwords_adapter)
            for check_class in (
                CompatibilityCheckWebsiteTracking,
                CompatibilityCheckECommerceTracking,
                CompatibilityCheckOnPagePhoneCallTracking,
            )
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['compatibility_checks'] = self.get_checks()
        return context


class QuoteView(UnpaidAccountRequiredMixin, DetailView):
    template_name = 'quotes/quote.html'
    context_object_name = 'quote'
    model = Quote

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except Http404:
            # If no quote exists, redirect to the start of the process.
            return HttpResponseRedirect(reverse('quoting_adwords_preamble'))

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Http404:
            # If no quote exists, redirect to the start of the process.
            return HttpResponseRedirect(reverse('quoting_adwords_preamble'))

        self.object.set_accepted()

        return HttpResponseRedirect(reverse('quoting_proceed_to_payment_gateway'))

    def get_object(self, queryset=None):
        # Get quote PK from the session.
        if queryset is None:
            queryset = self.get_queryset()

        if not self.request.session.get('quote_pk', None):
            raise Http404('No quote found in session')

        try:
            obj = queryset.get(pk=self.request.session['quote_pk'])
        except queryset.model.DoesNotExist:
            raise Http404('No {} found matching the query'.format(
                queryset.model._meta.verbose_name))
        return obj


class ProceedToPaymentGatewayView(PaymentDetailBaseView):
    template_name = 'quotes/proceed_to_payment_gateway.html'

    @cached_property
    def object(self):
        return self.get_object()

    def _create_payment(self):
        payment = self.model.objects.create(
            amount=0,
            action='VERIFY',
            currency_code='GBP',
            user=self.request.user,
        )

        if self.request.user.initial_continuous_authority_payment:
            self.request.user.previous_initial_continuous_authority_payments.add(
                self.request.user.initial_continuous_authority_payment)

        self.request.user.initial_continuous_authority_payment = payment
        self.request.user.save()

        return payment

    def get_object(self):
        if not hasattr(self, '_payment'):
            self._payment = self._create_payment()

        return self._payment


class PaymentFailedView(TemplateView):
    template_name = 'quotes/payment_failed.html'

    def dispatch(self, *args, **kwargs):
        # Disallow access to the page if there is no failed payment
        # to take care of.
        if self.request.user.has_payment_details:
            # 404 is appropriate in this case, as we're trying to act
            # upon a resource which doesn't exist; a failed payment.
            raise Http404

        # Restore the original initial continuous payment if it
        # existed, in case a user accidentally overwrites their
        # currently good card with a bad one.
        self.old_payment_reinstated = False
        previous_initial_CA_payments = self.request.user.previous_initial_continuous_authority_payments  # noqa
        if previous_initial_CA_payments.count():
            self.old_payment_reinstated = True
            previous_initial_CA_payment = previous_initial_CA_payments.last()
            previous_initial_CA_payments.remove(previous_initial_CA_payment)
            self.request.user.initial_continuous_authority_payment = previous_initial_CA_payment

            self.request.user.save()

        return super().dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        context.update({'old_payment_reinstated': self.old_payment_reinstated})

        return context
