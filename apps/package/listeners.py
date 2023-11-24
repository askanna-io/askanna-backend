from django.dispatch import receiver

from package.models import Package
from storage.signals import file_complete


@receiver(file_complete)
def extract_jobs_from_askanna_config(instance, created, **kwargs):
    """
    On file_complete signal and if the file is created for a Package, extract the jobs from the askanna.yml.

    Only do this if the file was not created. If the file was created & completed in the same request, the file is not
    linked yet to the Package model which will result in the AskAnna config not being available. This case is handled
    by the PackageCreateBaseSerializer.
    """
    if isinstance(instance.created_for, Package) and not created:
        instance.created_for.extract_jobs_from_askanna_config()
