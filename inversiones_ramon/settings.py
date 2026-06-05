# ══════════════════════════════════════════════════════════════
# settings.py — Configuración completa del proyecto
# Ubicación: inversiones_ramon/settings.py
# ══════════════════════════════════════════════════════════════

from pathlib import Path
import os

# ─────────────────────────────────────────────
# RUTAS BASE
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─────────────────────────────────────────────
# SEGURIDAD
# ─────────────────────────────────────────────
# ADVERTENCIA: cambiar antes de producción
SECRET_KEY = 'django-insecure-CAMBIA-ESTO-EN-PRODUCCION-usa-una-clave-larga-y-aleatoria'

# En producción: DEBUG = False
DEBUG = True

# En producción: ['tudominio.com', 'www.tudominio.com']
ALLOWED_HOSTS = ['*']

# ─────────────────────────────────────────────
# APLICACIONES
# ─────────────────────────────────────────────
INSTALLED_APPS = [
    # Apps de Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps del proyecto
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
# URLs
# ─────────────────────────────────────────────
ROOT_URLCONF = 'inversiones_ramon.urls'

# ─────────────────────────────────────────────
# TEMPLATES
# ─────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # templates globales opcionales
        'APP_DIRS': True,                   # busca en <app>/templates/
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Inyecta tasa BCV en todos los templates autenticados
                'core.context_processors.tasa_bcv',
            ],
        },
    },
]

WSGI_APPLICATION = 'inversiones_ramon.wsgi.application'

# ─────────────────────────────────────────────
# BASE DE DATOS
# SQLite para desarrollo — migrar a PostgreSQL en producción
# ─────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Configuración PostgreSQL (comentada — activar en producción)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME':     'inversiones_ramon_db',
#         'USER':     'postgres',
#         'PASSWORD': 'tu_password',
#         'HOST':     'localhost',
#         'PORT':     '5432',
#     }
# }

# ─────────────────────────────────────────────
# AUTENTICACIÓN
# ─────────────────────────────────────────────
AUTH_USER_MODEL = 'core.Usuario'   # modelo de usuario personalizado

LOGIN_URL           = '/login/'
LOGIN_REDIRECT_URL  = '/login/'
LOGOUT_REDIRECT_URL = '/login/'

# Token de reset de contraseña: 15 minutos
PASSWORD_RESET_TIMEOUT = 900

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─────────────────────────────────────────────
# CORREO ELECTRÓNICO — SMTP
# Usar para recuperación de contraseña
# ─────────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = 'tucorreo@gmail.com'       # ← cambiar
EMAIL_HOST_PASSWORD = 'tu_app_password_gmail'    # ← App Password de Google
DEFAULT_FROM_EMAIL  = 'Inversiones Ramón <tucorreo@gmail.com>'

# Durante desarrollo: mostrar emails en consola en vez de enviarlos
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

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
STATIC_ROOT = BASE_DIR / 'staticfiles'   # para collectstatic en producción

# STATICFILES_DIRS — crear carpeta 'static/' en la raíz si necesitas estáticos propios

# ─────────────────────────────────────────────
# MENSAJES (Bootstrap classes)
# ─────────────────────────────────────────────
from django.contrib.messages import constants as messages_constants

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
SESSION_COOKIE_AGE     = 28800      # 8 horas en segundos
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# ─────────────────────────────────────────────
# SEGURIDAD ADICIONAL (activar en producción)
# ─────────────────────────────────────────────
# SECURE_SSL_REDIRECT         = True
# SESSION_COOKIE_SECURE       = True
# CSRF_COOKIE_SECURE          = True
# SECURE_HSTS_SECONDS         = 3600
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True

# ─────────────────────────────────────────────
# CLAVE PRIMARIA POR DEFECTO
# ─────────────────────────────────────────────
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─────────────────────────────────────────────
# IVA CONFIGURABLE (porcentaje venezolano actual)
# ─────────────────────────────────────────────
IVA_PORCENTAJE = 16    # % — ajustar si cambia la ley

# ==============================================================================
# CONFIGURACIÓN DE LOGS PARA DETECTAR ERRORES OCULTOS EN LA BASE DE DATOS
# ==============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.db.backends': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}