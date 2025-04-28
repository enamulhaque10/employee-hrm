from django.apps import AppConfig


class BackupConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "aiz_backup"

    def ready(self):
        from django.urls import include, path

        from aiz.urls import urlpatterns

        urlpatterns.append(
            path("backup/", include("aiz_backup.urls")),
        )
        super().ready()
