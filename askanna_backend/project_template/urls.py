from django.conf.urls import url, include, re_path

from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter
from project_template.views import ProjectTemplateListView
from utils.urls import router

router.register(
    r"project_template", ProjectTemplateListView, basename="project_template"
)
urlpatterns = [
    re_path(r"^(?P<version>(v1|v2))/", include(router.urls)),
]
