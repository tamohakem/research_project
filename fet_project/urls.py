from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # Homepage
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    
    # Student redirect - /student/ goes to Academic Hub
    path('student/', RedirectView.as_view(url='/academics/hub/', permanent=False), name='student_redirect'),
    
    # App URLs
    path('accounts/', include('accounts.urls')),
    path('curriculum/', include('curriculum.urls')),
    path('academics/', include('academics.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('registration/', include('registration.urls')),
]

# Serve media files in debug mode
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)