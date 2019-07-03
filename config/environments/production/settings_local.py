DEBUG = True

ALLOWED_HOSTS = (
    'app.captivise.com',
)


# Database
# https://docs.djangoproject.com/en/1.10/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'captivise',
        'USER': 'captivise',
        'PASSWORD': 'D0yft8ymg7rJAj3EscTKTM3PoyS8X3nXB',
        'HOST': 'localhost',
        'PORT': '',
    },
}


# Email

EMAIL_HOST = 'mailtrap.io'
EMAIL_HOST_USER = '1999352a376c5581b'
EMAIL_HOST_PASSWORD = '3f2730828b18f1'
EMAIL_PORT = '2525'


# Googleads
ADWORDS_DEVELOPER_TOKEN = 'RAPXaNRd9Qsg08dOizs9NA'
ADWORDS_CLIENT_ID = '451839149375-d7cujajfgfgb2g7s2abp5l7pnuvi2vn1.apps.googleusercontent.com'
ADWORDS_SECRET_KEY = 'PaZFjB-9PVaHG66tGJC1nNhM'
ANALYTICS_TID = 'UA-107932867-1'


# django-compressor
COMPRESS_ENABLED = True


# Payment settings
ECOM6_PAYMENT_OPTIONS = {
    'default': {
        'merchant_ID': 109521,
        'secret_key': 'Talk12Top36Form',
        'country_code': 'gb',
    },
    'continuous_authority': {
        'merchant_ID': 109702,
        'secret_key': 'Talk12Top36Form',
        'country_code': 'gb',
    },
}

ECOM6_CALLBACK_SCHEME = 'https'
ECOM6_CALLBACK_HOST = 'app.captivise.com'


# Determines whether the environment should be able to make google ads
# changes.
SHOULD_MUTATE_GOOGLE_ADS = True
