from drf_yasg import openapi
from drf_yasg.views import get_schema_view


class OpenAPISchemaView(
    get_schema_view(
        openapi.Info(
            title="AskAnna API",
            default_version="v1",
            description="The AskAnna API can be used to interact with the AskAnna Backend.",
            terms_of_service="https://askanna.io/terms/",
        ),
        public=True,
    )
):
    pass
