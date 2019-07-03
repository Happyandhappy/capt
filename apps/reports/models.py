from django.conf import settings
from django.db import models

from model_utils import Choices


class Campaign(models.Model):
    is_managed = models.BooleanField(
        'Manage Using Captivise',
        default=False,
        choices=((True, 'Enabled'), (False, 'Disabled')),
    )
    max_cpc_limit = models.PositiveIntegerField(
        'Cost per Click (CPC) limit in £',
        default=10 * 10 ** 6,
        help_text='The maximum you would like to pay per click',
    )

    CYCLE_PERIOD_CHOICES = Choices(
        (30, '30 days', ),
        (60, '60 days', ),
        (180, '180 days', ),
        (365, '365 days', ),
    )
    cycle_period_days = models.PositiveIntegerField(
        'Cycle Period',
        default=30,
        choices=CYCLE_PERIOD_CHOICES,
        help_text='The time period with the most relevant data',
    )

    CONVERSION_TYPE_CPA = 'cpa'
    CONVERSION_TYPE_MARGIN = 'conversion_margin'
    CONVERSION_TYPE_CHOICES = (
        (CONVERSION_TYPE_CPA, 'Conversions by Lead Value'),
        (CONVERSION_TYPE_MARGIN, 'New - Conversions by Margins'),
    )
    conversion_type = models.CharField(
        max_length=17,
        choices=CONVERSION_TYPE_CHOICES,
        default=CONVERSION_TYPE_CPA,
    )
    target_cpa = models.PositiveIntegerField(
        'Target Cost per Acquisition (CPA) in £',
        default=0,
        help_text='The average amount you would like to pay for a conversion',
    )
    target_conversion_margin = models.DecimalField(
        'Target Margin in %',
        max_digits=5,
        decimal_places=3,
        default=0,
        help_text='The average margin you would like to achieve',
    )

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='campaigns')
    adwords_campaign_id = models.CharField(max_length=255)

    # Denormalised from the API
    title = models.CharField(max_length=255, blank=True)


class ScriptRun(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    increased_bids = models.PositiveIntegerField()
    decreased_bids = models.PositiveIntegerField()
    unchanged_bids = models.PositiveIntegerField()
    keywords_paused = models.PositiveIntegerField()
