from core.utils import remove_objects
from project.models import Project

from config.celery_app import app as celery_app


@celery_app.task(name="project.tasks.delete_projects")
def delete_projects():
    """
    We delete runs that are marked for deleted longer than 5 mins ago
    Also we check whether we don't have a deletion for the parent Workspace
    This will otherwise conflict with the Project deletion

    We pass on the queryset to get all objects
    these will be filtered in the function remove_objects to delete ones
    """
    remove_objects(Project.objects.filter(workspace__deleted__isnull=True))
