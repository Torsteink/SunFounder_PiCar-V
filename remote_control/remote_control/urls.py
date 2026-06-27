"""URL routes for the PiCar-V remote control app."""

from django.contrib import admin
from django.urls import path

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('run/', views.run, name='run'),
    path('cali/', views.cali, name='cali'),
    path('connection_test/', views.connection_test, name='connection_test'),
]
