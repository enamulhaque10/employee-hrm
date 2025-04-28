from django.urls import include, path

urlpatterns = [
    path("auth/", include("aiz_api.api_urls.auth.urls")),
    path("asset/", include("aiz_api.api_urls.asset.urls")),
    path("base/", include("aiz_api.api_urls.base.urls")),
    path("employee/", include("aiz_api.api_urls.employee.urls")),
    path("notifications/", include("aiz_api.api_urls.notifications.urls")),
    path("payroll/", include("aiz_api.api_urls.payroll.urls")),
    path("attendance/", include("aiz_api.api_urls.attendance.urls")),
    path("leave/", include("aiz_api.api_urls.leave.urls")),
]
