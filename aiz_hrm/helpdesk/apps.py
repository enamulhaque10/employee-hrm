from django.apps import AppConfig


class HelpdeskConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "helpdesk"

    def ready(self):
        from django.urls import include, path

        from aiz.aiz_settings import APPS
        from aiz.urls import urlpatterns

        APPS.append("helpdesk")
        urlpatterns.append(
            path("helpdesk/", include("helpdesk.urls")),
        )
        super().ready()
