class StatsRouter:
    """
    Redirect stats and metrics to statsdb
    """

    route_model_labels = {"runmetricsrow"}

    def db_for_read(self, model, **hints):
        """
        Attempts to read auth and contenttypes models go to auth_db.
        """
        print(model.__name__)
        if model.__name__.lower() in self.route_model_labels:
            print("here")
            return "stats"
        return "default"

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth and contenttypes models go to auth_db.
        """
        if model.__name__.lower() in self.route_model_labels:
            return "stats"
        return "default"

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        do_migrate = False
        if db == "default" and model_name not in self.route_model_labels:
            do_migrate = True
        if db == "stats" and model_name in self.route_model_labels:
            do_migrate = True

        if db == "stats":
            print(db, app_label, model_name, do_migrate)
        return do_migrate
