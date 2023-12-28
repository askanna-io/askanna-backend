from django_filters import FilterSet

from core.filters import MultiUpperValueCharFilter, MultiValueCharFilter
from run.models.run import STATUS_MAPPING


class MultiRunStatusFilter(MultiValueCharFilter):
    def filter(self, qs, value):
        if not value:
            # No point filtering if empty
            return qs

        # Map "external" status values to internal values
        mapped_values = []
        for v in value:
            for key, val in STATUS_MAPPING.items():
                if val == v:
                    mapped_values.append(key)

        if not mapped_values:
            # There are no valid values, so return an empty queryset
            return qs.none()

        return super().filter(qs, mapped_values)


class RunFilterSet(FilterSet):
    run_suuid = MultiValueCharFilter(
        field_name="suuid",
        help_text="Filter runs on a run suuid. For multiple values, separate the values with commas.",
    )
    run_suuid__exclude = MultiValueCharFilter(
        field_name="suuid",
        exclude=True,
        help_text="Exclude runs on a run suuid. For multiple values, separate the values with commas.",
    )

    status = MultiRunStatusFilter(
        field_name="status",
        help_text=(
            "Filter runs on a status. For multiple values, separate the values with commas."
            "</br><i>Available values:</i> queued, running, finished, failed"
        ),
    )
    status__exclude = MultiRunStatusFilter(
        field_name="status",
        exclude=True,
        help_text=(
            "Exclude runs on a status. For multiple values, separate the values with commas."
            "</br><i>Available values:</i> queued, running, finished, failed"
        ),
    )

    trigger = MultiUpperValueCharFilter(
        field_name="trigger",
        help_text=(
            "Filter runs on a trigger. For multiple values, separate the values with commas."
            "</br><i>Available values:</i> api, cli, python-sdk, webui, schedule, worker"
        ),
    )
    trigger__exclude = MultiUpperValueCharFilter(
        field_name="trigger",
        exclude=True,
        help_text=(
            "Exclude runs on a trigger. For multiple values, separate the values with commas."
            "</br><i>Available values:</i> api, cli, python-sdk, webui, schedule, worker"
        ),
    )

    job_suuid = MultiValueCharFilter(
        field_name="jobdef__suuid",
        help_text="Filter runs on a job suuid. For multiple values, separate the values with commas.",
    )
    job_suuid__exclude = MultiValueCharFilter(
        field_name="jobdef__suuid",
        exclude=True,
        help_text="Exclude runs on a job suuid. For multiple values, separate the values with commas.",
    )

    project_suuid = MultiValueCharFilter(
        field_name="jobdef__project__suuid",
        help_text="Filter runs on a project suuid. For multiple values, separate the values with commas.",
    )
    project_suuid__exclude = MultiValueCharFilter(
        field_name="jobdef__project__suuid",
        exclude=True,
        help_text="Exclude runs on a project suuid. For multiple values, separate the values with commas.",
    )

    workspace_suuid = MultiValueCharFilter(
        field_name="jobdef__project__workspace__suuid",
        help_text="Filter runs on a workspace suuid. For multiple values, separate the values with commas.",
    )
    workspace_suuid__exclude = MultiValueCharFilter(
        field_name="jobdef__project__workspace__suuid",
        exclude=True,
        help_text="Exclude runs on a workspace suuid. For multiple values, separate the values with commas.",
    )

    created_by_suuid = MultiValueCharFilter(
        field_name="created_by_member__suuid",
        help_text="Filter runs on a member suuid. For multiple values, separate the values with commas.",
    )
    created_by_suuid__exclude = MultiValueCharFilter(
        field_name="created_by_member__suuid",
        exclude=True,
        help_text="Exclude runs on a member suuid. For multiple values, separate the values with commas.",
    )

    package_suuid = MultiValueCharFilter(
        field_name="package__suuid",
        help_text="Filter runs on a package suuid. For multiple values, separate the values with commas.",
    )
    package_suuid__exclude = MultiValueCharFilter(
        field_name="package__suuid",
        exclude=True,
        help_text="Exclude runs on a package suuid. For multiple values, separate the values with commas.",
    )
