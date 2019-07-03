from django.conf.urls import url
from django.contrib.auth.views import (
    password_reset,
    password_reset_done,
    password_reset_confirm,
    password_reset_complete,
    logout,
)

from .forms import PasswordResetForm, SetPasswordForm
from .views import (
    AccountView,
    LoginView,
    AddAdwordsAccountView,
    AddAdwordsAccountCallbackView,
    RemoveAdwordsAccountView,
    AddAdwordsAccountClientCustomerView,
    RegisterView,
)

urlpatterns = [
    url(r'^login/$', LoginView.as_view(), name='accounts_login'),
    url(
        r'^logout/$',
        logout,
        {
            'next_page': 'accounts_login',
        },
        name='accounts_logout',
    ),
    url(r'^register/$', RegisterView.as_view(), name='accounts_register'),
    url(
        r'^password/reset/$',
        password_reset,
        {
            'template_name': 'accounts/password_reset.html',
            'email_template_name': 'accounts/email/password_reset.html',
            'post_reset_redirect': 'accounts_password_reset_done',
            'password_reset_form': PasswordResetForm,
        },
        name='accounts_password_reset',
    ),
    url(
        r'^password/reset/done/$',
        password_reset_done,
        {
            'template_name': 'accounts/password_reset_done.html',
        },
        name='accounts_password_reset_done',
    ),
    url(
        r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/'
        r'(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        password_reset_confirm,
        {
            'template_name': 'accounts/password_reset_confirm.html',
            'post_reset_redirect': 'accounts_password_reset_complete',
            'set_password_form': SetPasswordForm,
        },
        name='accounts_password_reset_confirm',
    ),
    url(
        r'^password/reset/complete/$',
        password_reset_complete,
        {
            'template_name': 'accounts/password_reset_complete.html',
        },
        name='accounts_password_reset_complete',
    ),
    url(r'^account/$', AccountView.as_view(), name='accounts_account'),
    url(
        r'^account/oauth/redirect/$',
        AddAdwordsAccountView.as_view(),
        name='accounts_oauth_redirect',
    ),
    url(
        r'^account/oauth/callback/$',
        AddAdwordsAccountCallbackView.as_view(),
        name='accounts_oauth_callback',
    ),
    url(
        r'^account/oauth/customers/$',
        AddAdwordsAccountClientCustomerView.as_view(),
        name='accounts_oauth_customers',
    ),
    url(
        r'^account/oauth/remove/$',
        RemoveAdwordsAccountView.as_view(),
        name='accounts_oauth_remove',
    ),
]
