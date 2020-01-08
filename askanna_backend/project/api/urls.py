from django.conf.urls import url

from project.api import views

urlpatterns = [
    url(
        r'^project/list$',
        views.ProjectListView.as_view(),
        name='project-list'
    ),
]
