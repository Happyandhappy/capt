import logging

from celery.task import task

from adwords.exceptions import TooEarlyError

from .models import User


@task(bind=True, name='accounts.charge_users')
def charge_users(self):
    logger = logging.getLogger('celery')

    for user in User.objects.filter(is_active=True):
        try:
            user.take_payment_if_required()
        except TooEarlyError as e:
            # Retry in an hour.
            self.retry(countdown=60*60, exc=e)
            break
        except Exception:
            logger.exception('Failed to take payment for user {pk}'.format(pk=user.pk))


@task(name='accounts.check_card_expiries')
def check_card_expiries():
    logger = logging.getLogger('celery')

    def alert_failed(user):
        logger.exception('Failed to alert user {pk} of imminent card expiry'.format(pk=user.pk))

    User.objects.lock_out_users_with_expired_cards()
    User.objects.alert_users_of_imminent_card_expiry(loghook=alert_failed)


@task(name='accounts.alert_user_registered')
def alert_user_registered(user_pk):
    User.objects.get(pk=user_pk).alert_user_registered()
