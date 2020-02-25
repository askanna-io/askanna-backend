from django.dispatch import receiver
from package.signals import package_upload_finish


@receiver(package_upload_finish)
def handle_upload(sender, signal, postheaders, **kwargs):
    print(sender)
    print(postheaders)
    print(kwargs)
    print("DISPATCH UPLOAD PROCESSING TO WORKER")