class HybridUUIDMixin:

    def get_parents_query_dict(self):
        query_dict = super().get_parents_query_dict()
        key = 'project__short_uuid'
        val = query_dict.get(key)
        if val and len(val) > 19:
            return {'project__pk': val}
        return query_dict
