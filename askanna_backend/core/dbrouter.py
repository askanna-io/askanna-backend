class StatsRouter:
    """
    Redirect stats and metrics to statsdb
    """

    route_model_labels = {"RunMetrics"}

    def db_for_read(self, model, **hints):
        """
        Attempts to read auth and contenttypes models go to auth_db.
        """
        print(model.__name__)
        if model.__name__ in self.route_model_labels:
            print("here")
            return "stats"
        return "default"

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth and contenttypes models go to auth_db.
        """
        if model.__name__ in self.route_model_labels:
            return "stats"
        return "default"

