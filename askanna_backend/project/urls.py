from django.contrib.auth.decorators import login_required
from django.conf.urls import url
from django.views.generic.base import RedirectView

from project import views

from project.api.urls import urlpatterns as api_urlpatterns

urlpatterns = [
] + api_urlpatterns
