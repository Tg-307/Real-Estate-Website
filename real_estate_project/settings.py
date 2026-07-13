"""
Real Estate Agency – Django Settings
Autumn theme | JWT auth | MySQL backend | Jazzmin admin
"""
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-autumn-real-estate-2024-change-in-production'

DEBUG = True

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    # Jazzmin must come before django.contrib.admin
    'jazzmin',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # Our apps
    'realestate',
    'api',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'real_estate_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'realestate' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'real_estate_project.wsgi.application'

# ── Database ────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'real_estate',
        'USER': 'root',
        'PASSWORD': 'Tanishk0823@',       # ← change to your MySQL password
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
    }
}

# ── Auth ────────────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'realestate.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 6}},
]

# ── REST Framework ──────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS':  True,
    'AUTH_HEADER_TYPES':      ('Bearer',),
}

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# ── Internationalisation ────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N      = True
USE_TZ        = False        # keep False so MySQL TIMESTAMP works naturally

# ── Static / Media ──────────────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'realestate' / 'static']

MEDIA_URL  = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Login / Logout ──────────────────────────────────────────────────────
LOGIN_URL          = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# ════════════════════════════════════════════════════════════════════════
#  JAZZMIN  –  Autumn theme admin
# ════════════════════════════════════════════════════════════════════════
JAZZMIN_SETTINGS = {
    "site_title":        "Real Estate Admin",
    "site_header":       "Real Estate Agency",
    "site_brand":        "🍂 RealtyCo",
    "site_logo":         None,
    "welcome_sign":      "Welcome to RealtyCo Admin",
    "copyright":         "RealtyCo IIIT Guwahati 2024",
    "search_model":      ["realestate.Property", "realestate.Customer"],
    "topmenu_links": [
        {"name": "Home",      "url": "admin:index"},
        {"name": "Website",   "url": "/dashboard/", "new_window": True},
        {"name": "API Docs",  "url": "/api/",       "new_window": True},
    ],
    "usermenu_links": [
        {"name": "Website",   "url": "/dashboard/", "new_window": True},
    ],
    "show_sidebar":              True,
    "navigation_expanded":       True,
    "icons": {
        "auth":                            "fas fa-users-cog",
        "realestate.User":                 "fas fa-user",
        "realestate.Branch":               "fas fa-building",
        "realestate.Employee":             "fas fa-user-tie",
        "realestate.Customer":             "fas fa-users",
        "realestate.Address":              "fas fa-map-marker-alt",
        "realestate.Property":             "fas fa-home",
        "realestate.PropertyImage":        "fas fa-images",
        "realestate.PotentialBuyer":       "fas fa-search",
        "realestate.BuyerInterest":        "fas fa-handshake",
        "realestate.Transaction":          "fas fa-file-invoice-dollar",
    },
    "default_icon_parents":  "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    "related_modal_active":  True,
    "custom_css":            "realestate/css/jazzmin_autumn.css",
    "custom_js":             None,
    "use_google_fonts_cdn":  True,
    "show_ui_builder":       True,
    "changeform_format":     "horizontal_tabs",
    "language_chooser":      False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text":     False,
    "footer_small_text":     False,
    "body_small_text":       False,
    "brand_small_text":      False,
    "brand_colour":          "navbar-warning",
    "accent":                "accent-warning",
    "navbar":                "navbar-dark",
    "no_navbar_border":      False,
    "navbar_fixed":          True,
    "layout_boxed":          False,
    "footer_fixed":          False,
    "sidebar_fixed":         True,
    "sidebar":               "sidebar-dark-warning",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style":  False,
    "sidebar_nav_flat_style":    False,
    "theme":                 "flatly",
    "dark_mode_theme":       None,
    "button_classes": {
        "primary":   "btn-warning",
        "secondary": "btn-secondary",
        "info":      "btn-info",
        "warning":   "btn-warning",
        "danger":    "btn-danger",
        "success":   "btn-success",
    },
}
