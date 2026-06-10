# ══════════════════════════════════════════════════════════════
# settings_prod.py — Sobreescrituras para PRODUCCIÓN
# Usar con: python manage.py runserver --settings=inversiones_ramon.settings_prod
# O definir:  DJANGO_SETTINGS_MODULE=inversiones_ramon.settings_prod
# ══════════════════════════════════════════════════════════════

from .settings import *          # hereda toda la config base
from decouple import config, Csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────────
# SEGURIDAD BÁSICA
# ─────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY')            # obligatorio en .env — sin default
DEBUG      = False
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())


# ─────────────────────────────────────────────
# MIDDLEWARE — WhiteNoise para archivos estáticos
# ─────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',   # ← justo después de Security
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


# ─────────────────────────────────────────────
# BASE DE DATOS — PostgreSQL
# ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     config('DB_NAME',     default='inversiones_ramon_db'),
        'USER':     config('DB_USER',     default='postgres'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST':     config('DB_HOST',     default='localhost'),
        'PORT':     config('DB_PORT',     default='5432'),
        'CONN_MAX_AGE': 60,    # reutiliza conexiones (mejora rendimiento)
    }
}


# ─────────────────────────────────────────────
# CORREO — SMTP real
# ─────────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = config('EMAIL_HOST',     default='smtp.gmail.com')
EMAIL_PORT          = config('EMAIL_PORT',     default=587,   cast=int)
EMAIL_USE_TLS       = config('EMAIL_USE_TLS',  default=True,  cast=bool)
EMAIL_HOST_USER     = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL',
                             default='Inversiones Ramón <noreply@inversionesramon.com>')


# ─────────────────────────────────────────────
# CABECERAS DE SEGURIDAD HTTPS
# ─────────────────────────────────────────────
SECURE_SSL_REDIRECT              = True
SESSION_COOKIE_SECURE            = True
CSRF_COOKIE_SECURE               = True
SECURE_BROWSER_XSS_FILTER        = True
SECURE_CONTENT_TYPE_NOSNIFF      = True
X_FRAME_OPTIONS                  = 'DENY'
SECURE_HSTS_SECONDS              = 31536000   # 1 año
SECURE_HSTS_INCLUDE_SUBDOMAINS   = True
SECURE_HSTS_PRELOAD              = True


# ─────────────────────────────────────────────
# SESIONES — cookies seguras
# ─────────────────────────────────────────────
SESSION_COOKIE_HTTPONLY          = True
CSRF_COOKIE_HTTPONLY             = True


# ─────────────────────────────────────────────
# LOGGING — archivo rotativo en producción
# ─────────────────────────────────────────────
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'prod': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_errors': {
            'class':       'logging.handlers.RotatingFileHandler',
            'filename':    LOG_DIR / 'errores.log',
            'maxBytes':    5 * 1024 * 1024,   # 5 MB
            'backupCount': 5,
            'formatter':   'prod',
        },
        'file_django': {
            'class':       'logging.handlers.RotatingFileHandler',
            'filename':    LOG_DIR / 'django.log',
            'maxBytes':    5 * 1024 * 1024,
            'backupCount': 3,
            'formatter':   'prod',
        },
    },
    'root': {
        'handlers': ['file_errors'],
        'level':    'ERROR',
    },
    'loggers': {
        'django': {
            'handlers':  ['file_django'],
            'level':     'WARNING',
            'propagate': False,
        },
        'django.request': {
            'handlers':  ['file_errors'],
            'level':     'ERROR',
            'propagate': False,
        },
    },
}
