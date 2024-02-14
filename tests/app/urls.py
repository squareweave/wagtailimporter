"""URL config."""
from django.urls import include, path
from wagtail.admin import urls as wagtailadmin_urls
from wagtail import urls as wagtail_urls

urlpatterns = [
    path(r'admin/', include(wagtailadmin_urls)),
    path(r'', include(wagtail_urls)),
]
