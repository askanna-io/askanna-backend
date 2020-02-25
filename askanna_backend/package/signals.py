import django.dispatch

package_upload_finish = django.dispatch.Signal(providing_args=["postheaders"])
