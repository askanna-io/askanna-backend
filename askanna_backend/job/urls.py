from django.conf.urls import url, include

from rest_framework import routers

from project.api.views import ProjectListView


router = routers.DefaultRouter()
router.register(r'jobaction', ProjectListView)

urlpatterns = [
    url(r'^v1/', include(router.urls)),
]
