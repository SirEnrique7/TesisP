# ══════════════════════════════════════════════════════════════
# settings.py — Configuración base del proyecto
# Desarrollo: funciona sin .env (usa valores por defecto)
# Producción: usa settings_prod.py + archivo .env
# ══════════════════════════════════════════════════════════════

from pathlib import Path
from django.contrib.messages import constants as messages_constants

try:
    from decouple import config, Csv
    _decouple_ok = True
except ImportError:
    _decouple_ok = False

BASE_DIR = Path(__file__).resolve().parent.parent


# ─────────────────────────────────────────────
# SEGURIDAD
# ─────────────────────────────────────────────
if _decouple_ok:
    SECRET_KEY    = config('SECRET_KEY', default='django-insecure-dev-key-change-in-production')
    DEBUG         = config('DEBUG', default=True, cast=bool)
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*', cast=Csv())
else:
    SECRET_KEY    = 'django-insecure-dev-key-change-in-production'
    DEBUG         = True
    ALLOWED_HOSTS = ['*']


# ─────────────────────────────────────────────
# APLICACIONES
# ─────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core',
    'inventario',
    'compras',
    'ventas',
    'reportes',
]


# ─────────────────────────────────────────────
# MIDDLEWARE
# ─────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ─────────────────────────────────────────────
# URLs Y WSGI
# ─────────────────────────────────────────────
ROOT_URLCONF       = 'inversiones_ramon.urls'
WSGI_APPLICATION   = 'inversiones_ramon.wsgi.application'


# ─────────────────────────────────────────────
# TEMPLATES
# ─────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.tasa_bcv',
            ],
        },
    },
]


# ─────────────────────────────────────────────
# BASE DE DATOS
# SQLite para desarrollo | PostgreSQL en producción
# ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ─────────────────────────────────────────────
# AUTENTICACIÓN
# ─────────────────────────────────────────────
AUTH_USER_MODEL      = 'core.Usuario'
LOGIN_URL            = '/login/'
LOGIN_REDIRECT_URL   = '/login/'
LOGOUT_REDIRECT_URL  = '/login/'
PASSWORD_RESET_TIMEOUT = 900   # 15 minutos

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ─────────────────────────────────────────────
# CORREO ELECTRÓNICO
# Desarrollo: muestra emails en la consola
# Producción: configurar en settings_prod.py o .env
# ─────────────────────────────────────────────
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# ─────────────────────────────────────────────
# INTERNACIONALIZACIÓN
# ─────────────────────────────────────────────
LANGUAGE_CODE = 'es-ve'
TIME_ZONE     = 'America/Caracas'
USE_I18N      = True
USE_TZ        = True


# ─────────────────────────────────────────────
# ARCHIVOS ESTÁTICOS
# ─────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'


# ─────────────────────────────────────────────
# MENSAJES (clases Bootstrap)
# ─────────────────────────────────────────────
MESSAGE_TAGS = {
    messages_constants.DEBUG:   'secondary',
    messages_constants.INFO:    'info',
    messages_constants.SUCCESS: 'success',
    messages_constants.WARNING: 'warning',
    messages_constants.ERROR:   'danger',
}


# ─────────────────────────────────────────────
# SESIONES
# ─────────────────────────────────────────────
SESSION_COOKIE_AGE              = 28800   # 8 horas
SESSION_EXPIRE_AT_BROWSER_CLOSE = True


# ─────────────────────────────────────────────
# NEGOCIO
# ─────────────────────────────────────────────
IVA_PORCENTAJE = 16   # % — ajustar si cambia la ley


# ─────────────────────────────────────────────
# DEFAULT PRIMARY KEY
# ─────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ─────────────────────────────────────────────
# LOGGING — solo errores reales en consola
# (sin spam de queries SQL en desarrollo)
# ─────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[{levelname}] {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
