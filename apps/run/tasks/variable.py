import datetime

from celery import shared_task

from run.models import RunVariable, RunVariableMeta


@shared_task(bind=True, name="run.tasks.extract_run_variable_meta")
def extract_run_variable_meta(self, variable_meta_uuid):
    """
    Extract meta data from run variables and store the meta data in run variable object
    """
    run_variable_meta = RunVariableMeta.objects.get(pk=variable_meta_uuid)
    run_variable_meta.update_meta()


@shared_task(bind=True, name="run.tasks.move_variables_to_rows")
def move_variables_to_rows(self, variable_meta_uuid):
    run_variable_meta = RunVariableMeta.objects.get(pk=variable_meta_uuid)

    # Remove old rows with source=run
    RunVariable.objects.filter(run=run_variable_meta.run).filter(
        label__contains=[
            {
                "name": "source",
                "value": "run",
                "type": "string",
            }
        ]
    ).delete()

    for variable in run_variable_meta.variables:
        variable["created_at"] = datetime.datetime.fromisoformat(variable["created_at"])
        variable["project_suuid"] = run_variable_meta.run.jobdef.project.suuid
        variable["job_suuid"] = run_variable_meta.run.jobdef.suuid
        variable["run_suuid"] = run_variable_meta.run.suuid
        variable["run"] = run_variable_meta.run

        RunVariable.objects.create(**variable)

    run_variable_meta.update_meta()


@shared_task(bind=True, name="run.tasks.post_run_deduplicate_variables")
def post_run_deduplicate_variables(self, run_uuid):
    """
    Remove double run variables if any
    """
    variables = RunVariable.objects.filter(run__pk=run_uuid).order_by("created_at", "label")
    last_variable = None
    for variable in variables:
        if last_variable and (
            variable.variable == last_variable.variable
            and variable.is_masked == last_variable.is_masked
            and variable.label == last_variable.label
            and variable.created_at == last_variable.created_at
        ):
            variable.delete()
        last_variable = variable

    try:
        run_variable = RunVariableMeta.objects.get(run__pk=run_uuid)
    except RunVariableMeta.DoesNotExist:
        pass
    else:
        run_variable.update_meta()
