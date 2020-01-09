from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions, authentication


class OpenAPISchemaView(get_schema_view(
    openapi.Info(
        title="AskAnna API",
        default_version='v1',
    ),
    public=True,
    # FIXME: do we want to require people to login?
    # permission_classes=(permissions.IsAuthenticated,),
    # authentication_classes=(authentication.SessionAuthentication,),
)):
    pass
