from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from run.models import Run, RunLog, RunVariable


@receiver(post_save, sender=Run)
def create_run_log_for_new_run_signal(sender, instance, created, **kwargs):
    """
    Create a RunLog everytime a Run gets created.
    """
    if created:
        try:
            RunLog.objects.create(run=instance)
        except Exception as exc:
            raise Exception(f"Issue creating a RunLog: {exc}") from exc


@receiver(pre_save, sender=RunVariable)
def mask_secret_variables(sender, instance, **kwargs):
    """
    We check if we should mask variables before saving them to the database. Additionally, we ensure that the label
    is_masked is added to the label list if the variable is masked.
    """
    if instance.is_masked is not True:
        variable_name = instance.variable.get("name").upper()
        is_masked = any(
            [
                "KEY" in variable_name,
                "TOKEN" in variable_name,
                "SECRET" in variable_name,
                "PASSWORD" in variable_name,
            ]
        )

        if is_masked:
            instance.is_masked = True

    if instance.is_masked:
        instance.variable["value"] = "***masked***"

        # Add label is_masked of type tag if the label is_masked is not in instance.label
        is_masked_label = {"name": "is_masked", "value": None, "type": "tag"}
        if not instance.label:
            instance.label = [is_masked_label]
        elif "is_masked" not in [label.get("name") for label in instance.label]:
            instance.label.append({"name": "is_masked", "value": None, "type": "tag"})
