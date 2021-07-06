# -*- coding: utf-8 -*-
import datetime
import json

from celery import shared_task

from job.models import (
    RunVariableRow,
    RunVariables,
)


@shared_task(bind=True, name="job.tasks.extract_variables_labels")
def extract_variables_labels(self, variables_uuid):
    """
    Extract labels in .variables and store the list of labels in .jobrun.labels
    """
    runvariables = RunVariables.objects.get(pk=variables_uuid)
    jobrun = runvariables.jobrun
    if not runvariables.variables:
        # we don't have variables stored, as this is None (by default on creation)
        return
    alllabels = []
    allkeys = []
    count = 0
    for variable in runvariables.variables[::]:
        labels = variable.get("label", [])
        for label_obj in labels:
            alllabels.append(label_obj.get("name"))

        # count number of variable
        variables = variable.get("variable", {})
        allkeys.append(variables.get("name"))
        count += 1

    # also count the ones in the databaase
    dbvariables = RunVariableRow.objects.filter(
        run_suuid=runvariables.short_uuid
    ).exclude(label__contains=[{"name": "source", "value": "run", "type": "string"}])
    for variable in dbvariables:
        labels = variable.label
        for label_obj in labels:
            alllabels.append(label_obj.get("name"))

        # count number of variable
        variables = variable.variable
        allkeys.append(variables.get("name"))
        count += 1

    jobrun.variable_keys = list(set(allkeys) - set([None]))
    jobrun.variable_labels = list(set(alllabels) - set([None]))
    jobrun.save(update_fields=["variable_labels", "variable_keys"])

    runvariables.count = count
    runvariables.size = len(json.dumps(runvariables.variables))
    runvariables.save(update_fields=["count", "size"])


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
