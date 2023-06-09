from django.conf.urls import include, url
from django.contrib import admin
from django.conf import settings

urlpatterns = [
    # Examples:
    # url(r'^$', 'deployerweb.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url(r'^$', 'deployerweb.views.list_configs', name='list_configs'),
    url(r'^login/$', 'deployerweb.views.login_page', {'document_root': settings.STATIC_ROOT}, name='login_page'),
    url(r'^authorize/$', 'deployerweb.views.authorize', name='authorize'),
    url(r'^logout/$', 'deployerweb.views.logout_page', name='logout_page'),
    url(r'^releases/$', 'deployerweb.views.list_dirs', name='list_dirs'),
    url(r'^components/$', 'deployerweb.views.list_dir_content', name='list_dir_content'),
    url(r'^deploy/$', 'deployerweb.views.deploy_it', name='deploy_it'),
    url(r'^status/$', 'deployerweb.views.deploys_status', name='deploys_status'),
    url(r'^logtail/$', 'deployerweb.views.get_log', name='get_log'),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT})
]
