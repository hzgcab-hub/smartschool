from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('accounts/', include('accounts.urls')),
    path('students/', include('students.urls')),
    path('teachers/', include('teachers.urls')),
    path('classes/', include('classes.urls')),
    path('academics/', include('academics.urls')),
    path('finance/', include('finance.urls')),
    path('library/', include('library.urls')),
    path('notices/', include('notices.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)