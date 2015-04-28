from django.conf.urls import include, url
from django.contrib import admin
import deployerweb.settings

urlpatterns = [
    # Examples:
    # url(r'^$', 'deployerweb.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', 'deployerweb.views.list_configs', name='list_configs'),
    url(r'^login/$', 'deployerweb.views.login_page', {'document_root': deployerweb.settings.STATIC_ROOT}, name='login_page'),
    url(r'^authorize/$', 'deployerweb.views.authorize', name='authorize'),
    url(r'^logout/$', 'deployerweb.views.logout_page', name='logout_page'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': deployerweb.settings.STATIC_ROOT})
]
