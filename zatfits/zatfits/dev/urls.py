import os
from django.conf.urls import *
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.contrib import admin
from dev.views import *
from servermanager.views import start_makehuman

urlpatterns = patterns('',
                       url(r'^admin/', include(admin.site.urls)),
                       url(r'^login/', connexion, name='login'),
                       url(r'^logout/', logout, name='logout'),
                       url(r'^help/', help, name='help'),
                       url(r'^account/', account, name='account'),
                       url(r'^contact/', contact, name='contact'),
                       url(r'^$', index, name='index'),
                       url(r'^fitting$', fitting, name='fitting'),
                       url(r'^model$', model, name='model'),
                       url(r'^startmk', start_makehuman, name='start_makehuman'),
                       url(r'^validate$', csrf_exempt(validate), name='validate'),
                       url(r'^scale$', csrf_exempt(scale), name='scale'),
                       url(r'^fittingScript$', csrf_exempt(fittingScript), name='fittingScript'),
                       url(r'^subscription$', subscription, name='subscription'),
                       )
