import datetime
import decimal
import logging
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ImproperlyConfigured
from django.core.mail import send_mail
from django.db import models
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

import requests

from adwords.adapter import Adapter
from adwords.exceptions import TooEarlyError
from billing.models import Payment
from billing.utils import get_pricing
from reports.utils import decimal_to_micro_amount, micro_amount_to_decimal
from website.utils import get_new_user_alert_email

from .exceptions import (
    CapturingContinuousAuthorityPaymentFailedError,
    NoContinuousAuthorityInitialPaymentError,
)
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    first_name = models.CharField(_('first name'), max_length=30, blank=True)
    last_name = models.CharField(_('last name'), max_length=30, blank=True)
    email = models.EmailField(_('email address'), unique=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    refresh_token = models.CharField(
        _('refresh token'),
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )
    client_customer_id = models.CharField(_('client customer id'), max_length=255, blank=True)
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)
    is_adwords_dry_run = models.BooleanField(_('Do not apply Adwords changes'), default=False)
    is_freerolled = models.BooleanField(
        _('Freeroll this user'),
        help_text=_(
            'If set, this user will have their account managed for free,'
            ' and will not encounter the payent step of the signup process.'
        ),
        default=False,
    )
    phone_number = models.CharField(_('Telephone'), max_length=14, blank=False)
    company_name = models.CharField(_('Company'), max_length=50, blank=True)
    email_confirmed_at = models.DateTimeField(_('Email confirmed at'), null=True, blank=True)
    initial_continuous_authority_payment = models.ForeignKey(
        'billing.Payment', null=True, blank=True, related_name='+')
    previous_initial_continuous_authority_payments = models.ManyToManyField(
        'billing.Payment', null=True, blank=True, related_name='+')
    payment_last_taken_at = models.DateField(auto_now_add=True)

    show_card_expiry_warning = models.BooleanField(default=False)

    google_analytics_client_id = models.UUIDField(
        _('The ID used to refer to this user within Google Analytics'),
        default=uuid.uuid4,
        unique=True,
    )

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def set_adwords_fields(self, refresh_token, client_customer_id):
        self.refresh_token = refresh_token
        self.client_customer_id = client_customer_id
        self.save()        

    def reset_adwords_fields(self):
        self.refresh_token = None
        self.client_customer_id = ''
        self.save()
    
    def getAdapter(self):
        return Adapter(self)

    @property
    def has_adwords_account(self):
        return self.refresh_token is not None

    @property
    def has_payment_details(self):
        if self.is_freerolled:
            return True

        payment = self.initial_continuous_authority_payment
        if payment is None:
            return False

        return payment.is_successful

    def get_payment_details_context(self):
        if self.is_freerolled:
            return {
                'card_number_mask': 'N/A',
                'card_expiry': 'N/A',
                'card_type': 'N/A',
            }

        payment = self.initial_continuous_authority_payment
        return {
            'card_number_mask': payment.response.card_number_mask,
            'card_expiry': '{month}/{year}'.format(
                month=payment.response.card_expiry_month,
                year=payment.response.card_expiry_year,
            ),
            'card_type': payment.response.card_type,
        }

    def get_payment_amount_required(self, force_recalculate=False):
        if hasattr(self, '_payment_amount_required') and not force_recalculate:
            return self._payment_amount_required

        now = datetime.datetime.now()
        if now.time() < datetime.time(hour=3):
            raise TooEarlyError(
                'Data is only available for the previous day from 3AM.'
                '  Please try again later.'
            )

        adapter = Adapter(self)
        monthly_spend = adapter.get_monthly_spend()

        spend_since_last_billed = adapter.get_spend_for_period(
            self.payment_last_taken_at, now.date())

        self._payment_amount_required = (
            spend_since_last_billed * get_pricing().get_fee(monthly_spend) / 100)
        print("Step Final")
        return self._payment_amount_required

    @property
    def is_payment_required(self):
        if self.is_freerolled:
            return False

        if datetime.datetime.now() - datetime.timedelta(days=30) > self.payment_last_taken_at:
            return True

        threshold = decimal_to_micro_amount(500)

        if threshold <= self.get_payment_amount_required():
            return True

        return False

    def take_payment(self, amount):
        if self.initial_continuous_authority_payment is None:
            raise NoContinuousAuthorityInitialPaymentError()

        if not self.initial_continuous_authority_payment.is_successful:
            raise NoContinuousAuthorityInitialPaymentError()

        payment = Payment.objects.create(
            amount=amount,
            currency_code='GBP',
            action='SALE',
            user=self,
        )

        payment.set_as_continuous_authority_payment(self.initial_continuous_authority_payment)
        payment.capture_continuous_authority_payment()

        if payment.response.response_code != 0:
            raise CapturingContinuousAuthorityPaymentFailedError(
                'Taking payment {payment_pk} for user {user_pk} failed.'.format(
                    payment_pk=payment.pk, user_pk=self.pk)
            )

        self.payment_last_taken_at = datetime.datetime.now()
        self.save()

        self.register_analytics_transaction(payment)

        del self._payment_amount_required

    def take_payment_if_required(self):
        if self.is_payment_required:
            amount = micro_amount_to_decimal(self.get_payment_amount_required)
            amount_in_pennies = int(amount * 100)

            return self.take_payment(amount_in_pennies)

    def register_analytics_transaction(self, payment):
        requests.post(
            'https://google-analytics.com/collect',
            data={
                'v': 1,
                'tid': settings.ANALYTICS_TID,
                'cid': self.google_analytics_client_id,
                't': 'transaction',
                'ti': payment.transaction_unique,
                'tr': decimal.Decimal(payment.amount) / 100,
                'ts': 0,
                'tt': 0,  # TODO:  If we charge VAT, this needs to change.
                'cu': 'GBP',
            },
        )

    def alert_user_registered(self):
        try:
            email_to = get_new_user_alert_email()
        except ImproperlyConfigured:
            logger = logging.getLogger('celery')
            logger.exception(
                'Failed to alert of a new user (pk: {pk}) registering;'
                ' no alert recipient set.'.format(pk=self.pk)
            )
        else:  # noexcept
            context = {
                "first_name": self.first_name,
                "last_name": self.last_name,
                "email": self.email,
                "company_name": self.company_name,
            }

            try:
                send_mail(
                    'Captivise - A new user has registered',
                    render_to_string('accounts/email/alert_user_registered.txt', context),
                    settings.DEFAULT_FROM_EMAIL,
                    [email_to],
                    fail_silently=False,
                )
            except Exception:
                logger = logging.getLogger('celery')
                logger.exception(
                    'Failed to alert of a new user (pk: {pk}) registering'.format(pk=self.pk))

    def save(self, *args, **kwargs):
        should_alert_user_registered = False
        if self.pk is None:
            should_alert_user_registered = True

        super().save(*args, **kwargs)

        if should_alert_user_registered:
            from .tasks import alert_user_registered
            alert_user_registered.apply_async((self.pk,))

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """
        Returns the short name for the user.
        """
        return self.first_name

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def set_email_confirmed(self, commit=True):
        self.email_confirmed_at = timezone.now()
        if commit:
            self.save()
