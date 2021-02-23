from django_filters import rest_framework as filters
from django_filters import CharFilter

from job.models import JobRun, RunMetricsRow


class RunFilter(filters.FilterSet):

    project = CharFilter(
        field_name="jobdef__project__short_uuid", method="filter_multiple"
    )
    job = CharFilter(field_name="jobdef__short_uuid", method="filter_multiple")
    runs = CharFilter(field_name="short_uuid", method="filter_multiple")

    def filter_multiple(self, queryset, name, value):
        """
        Create the field__in= filter to allow multi item lookup
        """
        values = list(map(lambda x: x.strip(), value.split(",")))
        field_name = f"{name}__in"
        return queryset.filter(**{field_name: values})

    class Meta:
        model = JobRun
        fields = ["short_uuid"]


class MetricFilter(filters.FilterSet):

    project = CharFilter(field_name="project_suuid", method="filter_multiple")
    job = CharFilter(field_name="job_suuid", method="filter_multiple")
    runs = CharFilter(field_name="run_suuid", method="filter_multiple")

    metric_name = CharFilter(field_name="metric__0__name")
    metric_value = CharFilter(field_name="metric__0__value")
    metric_type = CharFilter(field_name="metric__0__type")

    label_name = CharFilter(field_name="label__0__name")

    def filter_multiple(self, queryset, name, value):
        """
        Create the field__in= filter to allow multi item lookup
        """
        values = list(map(lambda x: x.strip(), value.split(",")))
        field_name = f"{name}__in"
        return queryset.filter(**{field_name: values})

    class Meta:
        model = RunMetricsRow
        fields = ["short_uuid"]
