from django.conf.urls import url, include
from django.urls import path, re_path, register_converter

from rest_framework import routers
from rest_framework.urlpatterns import format_suffix_patterns
from rest_framework_extensions.routers import ExtendedDefaultRouter as DefaultRouter

from job.views import JobActionView, StartJobView, ProjectJobViewSet, JobRunView
from project.api.views import ProjectListView
from project.api.views import ProjectListViewShort


class ShortUUIDConverter:
    regex = '[0-9a-zA-Z]{4}\-[0-9a-zA-Z]{4}\-[0-9a-zA-Z]{4}\-[0-9a-zA-Z]{4}'

    def to_python(self, value):
        return value
    
    def to_url(self, value):
        return value

register_converter(ShortUUIDConverter, 'shortuuid')

router = DefaultRouter()
(
    router
    .register(r"project", ProjectListViewShort, "project")
    .register(r"jobs", ProjectJobViewSet, "project-job", parents_query_lookups=["project__short_uuid"])
)


router.register(r"job", JobActionView)
router.register(r"jobrun", JobRunView)

urlpatterns = [
    url(r'^v1/', include(router.urls)),
    path(r'v1/run/<shortuuid:short_uuid>', StartJobView.as_view({'post': 'do_ingest_short'}), kwargs={'uuid': None}),
    path(r'v1/run/<uuid:uuid>', StartJobView.as_view({'post': 'do_ingest'}))
]
