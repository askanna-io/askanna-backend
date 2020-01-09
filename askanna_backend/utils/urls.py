from django.conf import settings
from django.urls import include, path, re_path, reverse_lazy
from django.views.generic import RedirectView

from django.conf.urls import url, include

from utils.views import OpenAPISchemaView

urlpatterns = [
    path(r'v1/', include([
        # Redirect to docs by default
        re_path(r'^$', RedirectView.as_view(
            url=reverse_lazy('schema-swagger-ui'),
            permanent=False)),

        # Swagger/OpenAPI documentation
        path(r'docs/', include([
            re_path(r'^swagger(?P<format>\.json|\.yaml)$',
                OpenAPISchemaView.without_ui(cache_timeout=0),
                name='schema-json'),
            path(r'swagger/',
                OpenAPISchemaView.with_ui('swagger', cache_timeout=0),
                name='schema-swagger-ui'),
            path(r'redoc/',
                OpenAPISchemaView.with_ui('redoc', cache_timeout=0),
                name='schema-redoc'),
        ])),
    ])),
]
