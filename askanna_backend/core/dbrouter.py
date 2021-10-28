class RunInfoRouter:
    """
    Redirect stats and metrics to runinfo
    """

    route_model_labels = {"runmetricsrow", "runvariablerow"}

    def db_for_read(self, model, **hints):
        """
        Attempts to read auth and contenttypes models go to auth_db.
        """
        if model.__name__.lower() in self.route_model_labels:
            return "runinfo"
        return "default"

    def db_for_write(self, model, **hints):
        """
        Attempts to write auth and contenttypes models go to auth_db.
        """
        if model.__name__.lower() in self.route_model_labels:
            return "runinfo"
        return "default"

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        do_migrate = False
        if db == "default" and model_name not in self.route_model_labels:
            do_migrate = True
        if db == "runinfo" and model_name in self.route_model_labels:
            do_migrate = True

        return do_migrate
