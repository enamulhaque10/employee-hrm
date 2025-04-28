from django.apps import AppConfig


class aizApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aiz_api"

    def ready(self):
        from django.urls import include, path

        from aiz.urls import urlpatterns

        urlpatterns.append(
            path("api/", include("aiz_api.urls")),
        )
        super().ready()
