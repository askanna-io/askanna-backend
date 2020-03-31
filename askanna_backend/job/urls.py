from django.conf.urls import url, include
from django.urls import path

from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter

from job.views import JobActionView, StartJobView, ProjectJobViewSet
from project.api.views import ProjectListViewShort

router = DefaultRouter()
(
    router
    .register(r"project", ProjectListViewShort, "project")
    .register(r"jobs", ProjectJobViewSet, "project-job", parents_query_lookups=["project__short_uuid"])
)


router.register(r"job", JobActionView)

urlpatterns = [
    url(r'^v1/', include(router.urls)),
    path(r'v1/run/<uuid:uuid>', StartJobView.as_view({'post': 'do_ingest'}))
]
