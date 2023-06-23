"""URL config."""
from wagtail import VERSION
from wagtail.admin import urls as wagtailadmin_urls
from django.conf.urls import include, 

if VERSION < (5,0):
    """URL config."""
    from django.conf.urls import url
    from wagtail.core import urls as wagtail_urls

    urlpatterns = [
        url(r'^admin/', include(wagtailadmin_urls)),
        url(r'', include(wagtail_urls)),
    ]
else:
    from django.urls import re_path
    from wagtail import urls as wagtail_urls

    urlpatterns = [
        re_path(r'^admin/', include(wagtailadmin_urls)),
        re_path(r'', include(wagtail_urls)),
    ]
