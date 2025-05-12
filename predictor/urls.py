from django.urls import path
from .views import PredictView, DashboardStatsView, DownloadReportView

urlpatterns = [
    path('', PredictView.as_view(), name='predict'),
    path('dashboard/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('download-report/', DownloadReportView.as_view(), name='download-report'),
]
