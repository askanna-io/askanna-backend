import datetime

from celery import shared_task
from run.models import RunVariable, RunVariableRow


@shared_task(bind=True, name="run.tasks.extract_run_variable_meta")
def extract_run_variable_meta(self, variables_uuid):
    """
    Extract meta data from run variables and store the meta data in run variable object
    """
    run_variable = RunVariable.objects.get(pk=variables_uuid)
    run_variable.update_meta()


@shared_task(bind=True, name="run.tasks.move_variables_to_rows")
def move_variables_to_rows(self, variables_uuid):
    run_variable = RunVariable.objects.get(pk=variables_uuid)

    # Remove old rows with source=run
    RunVariableRow.objects.filter(run_suuid=run_variable.short_uuid).filter(
        label__contains=[
            {
                "name": "source",
                "value": "run",
                "type": "string",
            }
        ]
    ).delete()

    for variable in run_variable.variables:
        variable["created"] = datetime.datetime.fromisoformat(variable["created"])
        variable["project_suuid"] = run_variable.run.jobdef.project.short_uuid
        variable["job_suuid"] = run_variable.run.jobdef.short_uuid
        # Overwrite run_suuid, even if the run_suuid defined is not right, prevent polution
        variable["run_suuid"] = run_variable.run.short_uuid

        RunVariableRow.objects.create(**variable)

    run_variable.update_meta()


@shared_task(bind=True, name="run.tasks.post_run_deduplicate_variables")
def post_run_deduplicate_variables(self, run_suuid):
    """
    Remove double run variables if any
    """
    variables = RunVariableRow.objects.filter(run_suuid=run_suuid).order_by("created", "label")
    last_variable = None
    for variable in variables:
        if last_variable and (
            variable.variable == last_variable.variable
            and variable.is_masked == last_variable.is_masked
            and variable.label == last_variable.label
            and variable.created == last_variable.created
        ):
            variable.delete()
        last_variable = variable

    try:
        run_variable = RunVariable.objects.get(run__short_uuid=run_suuid)
    except RunVariable.DoesNotExist:
        pass
    else:
        run_variable.update_meta()
