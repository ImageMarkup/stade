from .base import *

SECRET_KEY = "insecuresecret"
DEBUG = True
ALLOWED_HOSTS = []
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "stade",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "PORT": "5432",
    }
}
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
MEDIA_ROOT = '/uploads/'
MEDIA_URL = '/uploads/'
INSTALLED_APPS += ["debug_toolbar"]

MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")

INTERNAL_IPS = ["127.0.0.1", "0.0.0.0"]


def show_toolbar(request):
    return True


DEBUG_TOOLBAR_CONFIG = {'SHOW_TOOLBAR_CALLBACK': show_toolbar}
