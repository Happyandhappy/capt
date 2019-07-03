from django import forms
from django.contrib.auth import password_validation, get_user_model
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm as DjangoPasswordResetForm,
    UserCreationForm as DjangoUserCreationForm,
)

from adwords.adapter import Adapter
from adwords.exceptions import NonManagerAccountSelected, UserNotLinkedError


UserModel = get_user_model()


class LoginForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'Incorrect Login Details',
        'inactive': 'This account is inactive.',
    }


class PasswordResetForm(DjangoPasswordResetForm):
    email = forms.EmailField(label='Your Email Address', max_length=254)


class SetPasswordForm(forms.Form):
    new_password = forms.CharField(
        label='New password',
        widget=forms.PasswordInput,
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super(SetPasswordForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        password = self.cleaned_data['new_password']
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


class UserCreationForm(DjangoUserCreationForm):

    class Meta:
        model = UserModel
        fields = ('first_name', 'last_name', 'email', 'phone_number', 'company_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['first_name'].required = True
        self.fields['last_name'].required = True


class EditUserForm(forms.ModelForm):
    new_password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput,
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )

    class Meta:
        model = UserModel
        fields = ('email', )

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password')
        password_validation.validate_password(password, self.instance)
        return password

    def save(self, **kwargs):
        password = self.cleaned_data['new_password']
        if password:
            self.instance.set_password(password)
        return super().save(**kwargs)


class AdwordsClientCustomerForm(forms.Form):
    client_customer = forms.ChoiceField(choices=())

    def __init__(self, refresh_token=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['client_customer'].label = "Select Account"
        self.setup_customer_choices(refresh_token)

    def setup_customer_choices(self, refresh_token):
        try:
            try:
                # Try to get manager account
                customers = Adapter.get_customers(refresh_token)
                choices = [
                    (customer.customerId, customer.name)
                    for customer in customers
                    if not customer.canManageClients

                ]
            except:
                # In the event of failure, get normal
                customer = Adapter.get_customer(refresh_token)
                choices = [
                    (customer.customerId, customer.descriptiveName)
                ]
        except:
            raise NonManagerAccountSelected


        # Ignore manager accounts, as reports can't be run against them.
        # https://developers.google.com/adwords/api/docs/common-errors#ReportDefinitionError.CUSTOMER_SERVING_TYPE_REPORT_MISMATCH  # noqa
        
        self.fields['client_customer'].choices = choices
