from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def home(request):
    return JsonResponse({
        "status": "ok",
        "message": "UniGroups Backend Running 🚀"
    })

urlpatterns = [
    path('', home),  # <-- ADD THIS

    path('health/', home),

    path('admin/', admin.site.urls),

    path('api/auth/', include('users.urls')),
    path('api/groups/', include('groups.urls')),
    path('api/chat/', include('chat.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
