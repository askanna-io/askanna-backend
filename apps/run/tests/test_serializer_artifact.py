from unittest.mock import MagicMock

from run.serializers.artifact import ArtifactRelationSerializer, RunArtifactSerializer


def test_artifact_relation_serializer(test_run_artifacts):
    serializer = ArtifactRelationSerializer()
    serializer.instance = test_run_artifacts["artifact_1"]
    assert serializer.data == {
        "relation": "artifact",
        "suuid": test_run_artifacts["artifact_1"].suuid,
        "size": 606,
        "count_dir": 1,
        "count_files": 2,
    }


def test_run_artifact_serializer(test_run_artifacts):
    serializer = RunArtifactSerializer(context={"request": MagicMock()})
    serializer.instance = test_run_artifacts["artifact_1"]

    assert serializer.data.get("suuid") == test_run_artifacts["artifact_1"].suuid
    assert serializer.data.get("size") == 606
    assert serializer.data.get("count_dir") == 1
    assert serializer.data.get("count_files") == 2
