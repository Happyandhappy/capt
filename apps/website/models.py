from django.db import models


class SiteConfig(models.Model):
    new_user_alert_email = models.EmailField(
        help_text=(
            'The email address to which to send an email upon a new'
            ' user registering.  Leave blank to not send an email.'
        ),
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name_plural = 'site config'

    def save(self, *args, **kwargs):
        if self.__class__.objects.exclude(pk=self.pk).exists():
            raise ValueError(
                'There can be only one SiteConfig.  Please edit the existing one.')

        return super().save(*args, **kwargs)
