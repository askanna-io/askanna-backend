# -*- coding: utf-8 -*-
# from urllib.parse import urlencode
from rest_framework import serializers

from job.models import RunMetrics, RunMetricsRow


class RunMetricsSerializer(serializers.ModelSerializer):
    """Serializer for RunMetrics model.
    At this moment we take in as-is, no futher validation etc.
    """

    def to_representation(self, instance):
        #     """
        #     This is used in 'list' and 'detail' views
        #     """
        #     request = self.context.get("request")
        #     ordering = request.query_params.get("ordering", [])
        #     offset = request.query_params.get("offset", 0)
        #     limit = request.query_params.get("limit", 100)
        #     limit_or_offset = request.query_params.get(
        #         "offset"
        #     ) or request.query_params.get("limit")
        #     count = instance.count
        metrics = instance.metrics

        #     if ordering == "-metric.name":
        #         metrics = instance.get_sorted(reverse=True)

        #     if limit_or_offset:
        #         original_params = request.query_params.copy()
        #         # return paged metrics
        #         offset = int(offset)
        #         limit = int(limit)
        #         results = metrics

        #         if count:
        #             # are we having lines?
        #             results = metrics[offset : offset + limit]
        #         response_json = {
        #             "count": count,
        #             "results": results,
        #             "next": None,
        #             "previous": None,
        #         }

        #         scheme = request.scheme
        #         path = request.path
        #         host = request.META["HTTP_HOST"]

        #         if offset + limit < count:
        #             original_params["offset"] = offset + limit

        #             urlparams = urlencode(original_params)
        #             response_json["next"] = "{scheme}://{host}{path}?{params}".format(
        #                 scheme=scheme, host=host, path=path, params=urlparams
        #             )
        #         if offset - limit > -1:
        #             original_params["offset"] = offset - limit

        #             urlparams = urlencode(original_params)
        #             response_json["previous"] = "{scheme}://{host}{path}?{params}".format(
        #                 scheme=scheme, host=host, path=path, params=urlparams
        #             )
        #         return response_json

        #     # by default, return all metrics
        return metrics

    class Meta:
        model = RunMetrics
        fields = ["uuid", "short_uuid", "metrics"]
        read_only_fields = ["uuid", "short_uuid"]


class RunMetricsRowSerializer(serializers.ModelSerializer):
    """Serializer for RunMetricsRow model.
    """

    class Meta:
        model = RunMetricsRow
        fields = ["run_suuid", "metric", "label", "created"]
        read_only_fields = ["run_suuid"]
