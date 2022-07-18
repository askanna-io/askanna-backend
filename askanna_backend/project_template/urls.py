from django.conf.urls import include, re_path
from project_template.views import ProjectTemplateListView
from utils.urls import router

router.register(r"project_template", ProjectTemplateListView, basename="project_template")
urlpatterns = [
    re_path(r"^(?P<version>(v1))/", include(router.urls)),
]
