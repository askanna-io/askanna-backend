from core.filters import case_insensitive
from core.models import Setting


def test_filter_case_insensitive(db):
    data = ["Aa", "aa", "aA", "BB", "bb", "bB", "Bb", "Cc", "cc", "cC"]
    for name in data:
        Setting.objects.create(name=name)

    queryset_base = Setting.objects.all()
    assert queryset_base.count() == 10

    queryset = case_insensitive(queryset_base, "name", "aa")
    assert queryset.count() == 3
    for name in queryset.values_list("name", flat=True):
        assert name in ["Aa", "aa", "aA"]

    queryset = case_insensitive(queryset_base, "name", "AA")
    assert queryset.count() == 3
    for name in queryset.values_list("name", flat=True):
        assert name in ["Aa", "aa", "aA"]

    queryset = case_insensitive(queryset_base, "name", ["aa", "BB"])
    assert queryset.count() == 7
    for name in queryset.values_list("name", flat=True):
        assert name in ["Aa", "aa", "aA", "BB", "bb", "bB", "Bb"]
