from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
        url(r'^$', 'deployerweb.views.list_configs', name='list_configs'),
        url(r'^[\/]?list_dirs[\/]$', 'deployerweb.views.list_dirs', name='list_dirs'),
        url(r'^[\/]?list_dir/(?P<directory>.*)[\/]?', 'deployerweb.views.list_dir_contents', name='list_dir_contents'),
        url(r'^[\/]?deploy_component/[\/]?', 'deployerweb.views.deploy_component', name='deploy_component'),
        url(r'^[\/]?deploy_release/[\/]?', 'deployerweb.views.deploy_release', name='deploy_release'),
    # Examples:
    # url(r'^$', 'deployerweb.views.home', name='home'),
    # url(r'^deployerweb/', include('deployerweb.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
