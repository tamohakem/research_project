from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView, RedirectView

# ============================================================
# CUSTOMIZE DJANGO ADMIN INTERFACE
# ============================================================
admin.site.site_header = "FET Academic Tracking System Administration"
admin.site.site_title = "FET Academic Tracking System"
admin.site.index_title = "Welcome to FET Academic Tracking System"
admin.site.site_url = "/dashboard/"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('student/', RedirectView.as_view(url='/academics/hub/', permanent=False), name='student_redirect'),
    path('accounts/', include('accounts.urls')),
    path('curriculum/', include('curriculum.urls')),
    path('academics/', include('academics.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('registration/', include('registration.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    