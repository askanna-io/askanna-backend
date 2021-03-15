from django_filters import rest_framework as filters
from django_filters import CharFilter
import django_filters

from django_filters.constants import EMPTY_VALUES
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


class MetricDataFilter(django_filters.OrderingFilter):

    custom_ordering = [
        ("metric.name", "Metric name", "metric__0__name"),
        ("metric.value", "Metric value", "metric__0__value"),
        ("metric.type", "Metric type", "metric__0__type"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for ordering in self.custom_ordering:
            self.extra["choices"] += [
                (ordering[0], ordering[1]),
                ("-" + ordering[0], ordering[1] + " (descending)"),
            ]
        # self.extra['choices'] += [
        #     ("metric.name", "Metric name"),
        #     ("-metric.name", "Metric name"),
        #     ("metric.value", "Metric value"),
        #     ("-metric.value", "Metric value"),
        #     ("metric.type", "Metric type"),
        #     ("-metric.type", "Metric type"),
        # ]

    def filter(self, qs, value):
        if value in EMPTY_VALUES:
            return qs
        ordering_keys = list(map(lambda x: x[0], self.custom_ordering))
        ordering_keys += list(map(lambda x: "-" + x[0], self.custom_ordering))

        selected_custom_order_filter = list(set(value) & set(ordering_keys))
        if selected_custom_order_filter:
            # build query
            ordering = []
            for v in value:
                if v in selected_custom_order_filter:
                    descending = v.startswith("-")
                    param = v[1:] if descending else v
                    # find field to sort on
                    field_name = [
                        order[2] for order in self.custom_ordering if order[0] == param
                    ][0]
                    ordering.append("-%s" % field_name if descending else field_name)
            return qs.order_by(*ordering)

        return super().filter(qs, value)


class MetricFilter(filters.FilterSet):

    project = CharFilter(field_name="project_suuid", method="filter_multiple")
    job = CharFilter(field_name="job_suuid", method="filter_multiple")
    runs = CharFilter(field_name="run_suuid", method="filter_multiple")

    metric_name = CharFilter(field_name="metric__0__name")
    metric_value = CharFilter(field_name="metric__0__value")
    metric_type = CharFilter(field_name="metric__0__type")

    label_name = CharFilter(field_name="label__*__name", method="filter_array")
    label_value = CharFilter(field_name="label__*__value", method="filter_array")
    label_type = CharFilter(field_name="label__*__type", method="filter_array")

    ordering = MetricDataFilter(fields=(("created", "created"),))

    def filter_multiple(self, queryset, name, value):
        """
        Create the field__in= filter to allow multi item lookup
        """
        values = list(map(lambda x: x.strip(), value.split(",")))
        field_name = f"{name}__in"
        return queryset.filter(**{field_name: values})

    def filter_array(self, queryset, name, value):
        """
        Create the __contains=[{"field": "value"}] lookup
        """
        field = name.split("__*__")[0]
        subfield = name.split("__*__")[1]
        query_field = "{}__contains".format(field)
        return queryset.filter(**{query_field: [{subfield: value}]})

    class Meta:
        model = RunMetricsRow
        fields = ["short_uuid"]
