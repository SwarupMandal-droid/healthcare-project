import os
import warnings
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# ✅ SECURITY: Secret key MUST be set in .env
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError('SECRET_KEY environment variable must be set')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

# ✅ SECURITY: Only allow specified hosts
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')

# ✅ All our apps registered
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'axes',  # Rate limiting and security
    # Our apps
    'accounts',
    'patients',
    'doctors',
    'appointments',
    'payments',
    'ai_assistant',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',  # Rate limiting
]

ROOT_URLCONF = 'lifeline_care.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],   # ← Global templates folder
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'patients.context_processors.appointment_badge',
            ],
        },
    },
]

# ✅ Database - Supports both MySQL (local) and PostgreSQL (Railway)
# Railway provides a DATABASE_URL env var automatically when you add a PostgreSQL plugin
if os.getenv('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(default=os.getenv('DATABASE_URL'), conn_max_age=600)
    }
else:
    # Fallback to local MySQL for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT', '3306'),
        }
    }
    if not all([DATABASES['default']['NAME'], DATABASES['default']['USER'],
               DATABASES['default']['PASSWORD'], DATABASES['default']['HOST']]):
        raise ValueError('Database credentials must be set in .env')

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'   # ← Set to India timezone
USE_I18N = True
USE_TZ = True

# ✅ Static and Media files
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ✅ Auth redirect settings
LOGIN_URL = '/accounts/auth/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/auth/'

# ✅ Razorpay - Credentials from environment
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET')
RAZORPAY_WEBHOOK_SECRET = os.environ.get('RAZORPAY_WEBHOOK_SECRET')

if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
    warnings.warn('Razorpay credentials not set — payment features will be unavailable')

# ✅ Anthropic API Key
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
if not ANTHROPIC_API_KEY:
    warnings.warn('ANTHROPIC_API_KEY not set — AI assistant will be unavailable')

# ✅ CSRF Trusted Origins (required for Railway)
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost').split(',')

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# ✅ SECURITY: Session settings
SESSION_COOKIE_SECURE = not DEBUG  # HTTPS only in production
SESSION_COOKIE_HTTPONLY = True  # No JavaScript access
SESSION_COOKIE_SAMESITE = 'Strict'

# ✅ SECURITY: CSRF settings
CSRF_COOKIE_SECURE = not DEBUG  # HTTPS only in production
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# ✅ SECURITY: Rate limiting with django-axes
AXES_FAILURE_LIMIT = 5  # Lock account after 5 failed attempts
AXES_COOLOFF_DURATION = 30  # Minutes
AXES_LOCK_OUT_AT_FAILURE = True
AXES_LOCKOUT_TEMPLATE = 'security/lockout.html'

# ✅ SECURITY: Authentication backends for rate limiting
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # Rate limiting
    'django.contrib.auth.backends.ModelBackend',  # Default Django backend
]

# ✅ SECURITY: Content Security
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_SECURITY_POLICY = {
    'default-src': ("'self'",),
    'script-src': ("'self'", 'cdnjs.cloudflare.com'),
    'style-src': ("'self'", 'cdnjs.cloudflare.com', 'fonts.googleapis.com'),
    'font-src': ("'self'", 'fonts.gstatic.com'),
}