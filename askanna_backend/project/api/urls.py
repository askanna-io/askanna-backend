from django.conf.urls import url, include, re_path

from rest_framework import routers

from project.api.views import ProjectListView, ProjectListViewShort


router = routers.DefaultRouter()
# router.register(r'project', ProjectListView)
router.register(r'project', ProjectListViewShort)

urlpatterns = [
    re_path(r'^(?P<version>(v1|v2))/', include(router.urls)),
]
