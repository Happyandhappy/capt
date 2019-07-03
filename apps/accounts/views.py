from django.conf import settings
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, FormView, UpdateView, View

from googleads import oauth2
from oauth2client import client

from adwords.exceptions import NonManagerAccountSelected
from website.utils import get_adwords_client
from website.views import ActiveMenuItemMixin

from .forms import EditUserForm, LoginForm, AdwordsClientCustomerForm, UserCreationForm


class PaidAccountRequiredMixin(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.has_payment_details

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('quoting_adwords_preamble'))
        else:
            return HttpResponseRedirect(reverse('accounts_login'))


class UnpaidAccountRequiredMixin(UserPassesTestMixin):

    def test_func(self):
        return self.request.user.is_authenticated and not self.request.user.has_payment_details

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            return HttpResponseRedirect(reverse('reports_dashboard'))
        else:
            return HttpResponseRedirect(reverse('accounts_login'))


class LoginView(FormView):
    template_name = 'accounts/login.html'
    form_class = LoginForm

    def form_valid(self, form):
        login(self.request, form.get_user())
        return super().form_valid(form)

    def get_success_url(self):
        next_url = self.request.GET.get('next', '')
        # Only accept internal links.
        if next_url.startswith('/') and not next_url.startswith('//'):
            return next_url

        return reverse_lazy('reports_dashboard')


class RegisterView(CreateView):
    template_name = 'accounts/register.html'
    form_class = UserCreationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response

    def get_success_url(self):
        return reverse_lazy('quoting_adwords_preamble')


class AccountView(ActiveMenuItemMixin, LoginRequiredMixin, PaidAccountRequiredMixin, UpdateView):
    template_name = 'accounts/accounts.html'
    form_class = EditUserForm

    def get_active_menu(self):
        return {
            'accounts': True,
        }

    def get_adwords_account_details(self, user):
        adwords_client = get_adwords_client(user.refresh_token, user.client_customer_id)

        customers = adwords_client.GetService('CustomerService').getCustomers()

        for customer in customers:
            if customer.customerId == int(user.client_customer_id):
                return customer

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'has_adwords_account': self.request.user.has_adwords_account,
            'has_payment_details': self.request.user.has_payment_details,
        })

        if self.request.user.has_adwords_account:
            # TODO Should this be cached somehow?
            context.update({
                'adwords_account': self.get_adwords_account_details(self.request.user)
            })

        if self.request.user.has_payment_details:
            context.update(self.request.user.get_payment_details_context())

        return context

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        self.object = form.save()
        update_session_auth_hash(self.request, self.object)
        return self.form_invalid(form)


class RemoveAdwordsAccountView(LoginRequiredMixin, PaidAccountRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        request.user.reset_adwords_fields()

        return HttpResponseRedirect(reverse('accounts_account'))


class BaseAdwordsAccountView(View):

    def get_adwords_client(self, request):
        client_id = settings.ADWORDS_CLIENT_ID
        client_secret = settings.ADWORDS_SECRET_KEY
        redirect_uri = request.build_absolute_uri(reverse('accounts_oauth_callback'))

        return client.OAuth2WebServerFlow(
            client_id=client_id,
            client_secret=client_secret,
            scope=oauth2.GetAPIScope('adwords'),
            user_agent='Test',
            prompt='consent',
            redirect_uri=redirect_uri,
        )


class AddAdwordsAccountView(BaseAdwordsAccountView):

    def get(self, request, *args, **kwargs):
        flow = self.get_adwords_client(request)

        auth_uri = flow.step1_get_authorize_url()

        return HttpResponseRedirect(auth_uri)


class AddAdwordsAccountCallbackView(BaseAdwordsAccountView):

    def get(self, request, *args, **kwargs):
        flow = self.get_adwords_client(request)

        auth_code = request.GET.get('code', None)

        credentials = flow.step2_exchange(auth_code)

        refresh_token = credentials.refresh_token

        request.session['refresh_token'] = refresh_token

        return HttpResponseRedirect(reverse('accounts_oauth_customers'))


class AddAdwordsAccountClientCustomerView(LoginRequiredMixin, FormView):
    template_name = 'accounts/account_add_client_customers.html'
    form_class = AdwordsClientCustomerForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        kwargs.update({
            'refresh_token': self.request.session['refresh_token'],
        })

        return kwargs

    def get_form(self, form_class=None):
        if form_class is None:
            form_class = self.get_form_class()

        try:
            form = form_class(**self.get_form_kwargs())
        except NonManagerAccountSelected:
            return None

        return form

    def get_success_url(self):        
        if self.request.user.has_payment_details:            
            return reverse('accounts_account')
        else:            
            return reverse('quoting_compatibility_results')

    def form_valid(self, form):        
        self.request.user.set_adwords_fields(
            refresh_token=self.request.session['refresh_token'],
            client_customer_id=form.cleaned_data['client_customer'],
        )
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if context['form'] is None:
            context['non_manager_account_selected'] = True
        return context
