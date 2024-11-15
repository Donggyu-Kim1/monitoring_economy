# markets/urls.py
from django.urls import path
from . import views

app_name = "markets"

urlpatterns = [
    # 메인 대시보드
    path("", views.DashboardView.as_view(), name="dashboard"),
    # 상세 페이지
    path("indices/", views.MarketIndexListView.as_view(), name="indices"),
    path("bonds/", views.BondYieldListView.as_view(), name="bonds"),
    path("exchange/", views.ExchangeRateListView.as_view(), name="exchange"),
    path("commodities/", views.CommodityListView.as_view(), name="commodities"),
    path("calendar/", views.EconomicCalendarView.as_view(), name="calendar"),
    path("news/", views.NewsListView.as_view(), name="news"),
    # API 엔드포인트
    path("api/latest/", views.get_latest_data, name="api-latest"),
    path("api/chart/<str:chart_type>/", views.get_chart_data, name="api-chart"),
]
