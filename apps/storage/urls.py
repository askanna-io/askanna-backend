from core.urls import router
from storage.views import FileViewSet

router.register(
    r"storage/file",
    FileViewSet,
    basename="storage-file",
)

urlpatterns = []
