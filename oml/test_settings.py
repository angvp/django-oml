DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

INSTALLED_APPS = [
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'oml',
]

MIDDLEWARE = []
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
SECRET_KEY = 'this-is-just-for-tests-so-not-that-secret'
OML_CONFIG = {
    'OML_EXCLUDE_MODERATED': True,
    'OML_EXCLUDED_GROUPS': [1],
}
