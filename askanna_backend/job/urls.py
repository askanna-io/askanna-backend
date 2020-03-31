from django.conf.urls import url, include

from rest_framework import routers
from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter

from job.views import JobActionView, ProjectJobViewSet
from project.api.views import ProjectListView

router = routers.DefaultRouter()

router = DefaultRouter()
(
    router
    .register(r"project", ProjectListView, "project")
    .register(r"jobs", ProjectJobViewSet, "project-job", parents_query_lookups=["project"])
)


router.register(r"job", JobActionView)

urlpatterns = [
    url(r"^v1/", include(router.urls)),
]
