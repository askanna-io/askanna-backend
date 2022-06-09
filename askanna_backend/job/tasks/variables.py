# -*- coding: utf-8 -*-
import datetime

from celery import shared_task

from job.models import (
    RunVariableRow,
    RunVariables,
)


@shared_task(bind=True, name="job.tasks.extract_variables_meta")
def extract_variables_meta(self, variables_uuid):
    """
    Extract labels in .variables and store the list of labels in .jobrun.labels
    """
    runvariables = RunVariables.objects.get(pk=variables_uuid)
    runvariables.update_meta()


@shared_task(bind=True, name="job.tasks.move_variables_to_rows")
def move_variables_to_rows(self, variables_uuid):
    runvariables = RunVariables.objects.get(pk=variables_uuid)

    # remove old rows with source=run
    RunVariableRow.objects.filter(run_suuid=runvariables.short_uuid).filter(
        label__contains=[{"name": "source", "value": "run", "type": "string"}]
    ).delete()

    for variable in runvariables.variables:
        variable["created"] = datetime.datetime.fromisoformat(variable["created"])
        variable["project_suuid"] = runvariables.jobrun.jobdef.project.short_uuid
        variable["job_suuid"] = runvariables.jobrun.jobdef.short_uuid
        # overwrite run_suuid, even if the run_suuid defined is not right, prevent polution
        variable["run_suuid"] = runvariables.jobrun.short_uuid

        RunVariableRow.objects.create(**variable)

    runvariables.update_meta()


@shared_task(bind=True, name="job.tasks.post_run_deduplicate_variables")
def post_run_deduplicate_variables(self, run_suuid):
    """
    Remove double run variables if any
    """
    variables = RunVariableRow.objects.filter(run_suuid=run_suuid).order_by("created")
    last_variable = None
    for variable in variables:
        if variable == last_variable:
            variable.delete()
        last_variable = variable

    runvariables = RunVariables.objects.get(jobrun__short_uuid=run_suuid)
    runvariables.update_meta()
