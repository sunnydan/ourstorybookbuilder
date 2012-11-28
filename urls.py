from django.conf.urls.defaults import *
from views import *
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import login, logout

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', landing_page),
    url(r'^login/$', login),
    url(r'^logout/$', logout, {'next_page': '/'}),
    url(r'^register/$', register),
    url(r'^branch/$', convert_request_to_url),
    url(r'^branch/(\d+)/$', serve_branch_by_id),
    url(r'^edit/$', convert_request_to_url),
    url(r'^kill/$', kill_branch),
    url(r'^branch/(\d*)[-]([A-Za-z]?.*)/$', serve_branch),
    url(r'^learnmore/$', learnmore),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'userpage/$', userpage),
    url(r'userpage/(.+)/$', other_userpage),
    url(r'edit/(\d*)[-]([A-Za-z]?.*)/$', edit_branch),
    url(r'vote/(\d*)[-]([A-Za-z]?.*)/$', vote_processor),
    url(r'search/$', convert_request_to_url),
    url(r'search/(.+)/$', search),

    # url(r'^account/$', account),
    # url(r'^accounts/profile/$', edit_account),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
     url(r'^admin/', include(admin.site.urls)),
     (r'^media/(?P<path>.*)$', 'django.views.static.serve',
       {'document_root': settings.MEDIA_ROOT}),
)
