import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'unigroups_project.settings')
application = get_wsgi_application()

# WhiteNoise — serves static files in production without a CDN
try:
    from whitenoise import WhiteNoise
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parent.parent
    application = WhiteNoise(application, root=str(BASE_DIR / 'staticfiles'))
except Exception:
    pass
