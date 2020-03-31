from django.conf.urls import url, include

from rest_framework import routers

from project.api.views import ProjectListView, ProjectListViewShort


router = routers.DefaultRouter()
# router.register(r'project', ProjectListView)
router.register(r'project', ProjectListViewShort)

urlpatterns = [
    url(r'^v1/', include(router.urls)),
]
