from django.views.generic import TemplateView, ListView, DetailView
from django.utils import timezone
from django.db.models import F
from django.http import JsonResponse
from django.core.cache import cache  # 추가
from datetime import timedelta, datetime
from .tasks import collect_historical_data  # tasks.py의 함수도 import
from .models import (
    MarketIndex,
    BondYield,
    ExchangeRate,
    Commodity,
    EconomicCalendar,
    NewsHeadline,
)
import logging
import yfinance as yf

# API Views for AJAX requests
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class DashboardView(TemplateView):
    template_name = "markets/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 최신 데이터 조회
        context["market_data"] = MarketIndex.objects.first()
        context["bond_data"] = BondYield.objects.first()
        context["exchange_data"] = ExchangeRate.objects.first()
        context["commodity_data"] = Commodity.objects.first()

        # 최근 뉴스 헤드라인
        context["news"] = NewsHeadline.objects.all()[:5]

        # 오늘/이번 주 예정된 경제지표
        today = timezone.now().date()
        week_end = today + timedelta(days=7)
        context["economic_calendar"] = EconomicCalendar.objects.filter(
            release_date__range=[today, week_end]
        ).order_by("release_date")

        # 데이터 갱신 시간
        if context["market_data"]:
            context["last_update"] = context["market_data"].timestamp

        return context


class MarketIndexListView(ListView):
    model = MarketIndex
    template_name = "markets/market_index_list.html"
    context_object_name = "indices"
    paginate_by = 20
    ordering = ["-timestamp"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 전일 대비 변화율 계산
        if self.object_list:
            latest = self.object_list[0]
            try:
                previous = MarketIndex.objects.filter(
                    timestamp__lt=latest.timestamp
                ).first()

                if previous:
                    context["changes"] = {
                        "sp500": calculate_change(latest.sp500, previous.sp500),
                        "nasdaq": calculate_change(latest.nasdaq, previous.nasdaq),
                        "kospi": calculate_change(latest.kospi, previous.kospi),
                        "kosdaq": calculate_change(latest.kosdaq, previous.kosdaq),
                        "vix": calculate_change(latest.vix, previous.vix),
                        "dxy": calculate_change(latest.dxy, previous.dxy),
                    }
            except Exception as e:
                context["error"] = str(e)

        return context


class BondYieldListView(ListView):
    model = BondYield
    template_name = "markets/bond_yield_list.html"
    context_object_name = "yields"
    paginate_by = 20
    ordering = ["-timestamp"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 스프레드 추이 데이터 추가
        context["spread_data"] = self.model.objects.values(
            "timestamp", "us_spread"
        ).order_by("-timestamp")[:30]
        return context


class ExchangeRateListView(ListView):
    model = ExchangeRate
    template_name = "markets/exchange_rate_list.html"
    context_object_name = "rates"
    paginate_by = 20
    ordering = ["-timestamp"]


class CommodityListView(ListView):
    model = Commodity
    template_name = "markets/commodity_list.html"
    context_object_name = "commodities"
    paginate_by = 20
    ordering = ["-timestamp"]


class EconomicCalendarView(ListView):
    model = EconomicCalendar
    template_name = "markets/economic_calendar.html"
    context_object_name = "events"

    def get_queryset(self):
        # 지난 일주일과 향후 한 달의 일정 표시
        today = timezone.now().date()
        past_week = today - timedelta(days=7)
        next_month = today + timedelta(days=30)
        return self.model.objects.filter(
            release_date__range=[past_week, next_month]
        ).order_by("release_date")


class NewsListView(ListView):
    model = NewsHeadline
    template_name = "markets/news_list.html"
    context_object_name = "headlines"
    paginate_by = 15
    ordering = ["-timestamp"]


# Utility functions
def calculate_change(current, previous):
    """변화율 계산"""
    if not (current and previous):
        return None
    try:
        change = ((current - previous) / previous) * 100
        return round(change, 2)
    except ZeroDivisionError:
        return None


def get_latest_data(request):
    """최신 데이터 JSON 응답"""
    try:
        data = {
            "market": MarketIndex.objects.values().first(),
            "bonds": BondYield.objects.values().first(),
            "exchange": ExchangeRate.objects.values().first(),
            "commodities": Commodity.objects.values().first(),
            "timestamp": timezone.now().isoformat(),
        }
        return JsonResponse({"data": data})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def get_chart_data(request, chart_type):
    """차트 데이터 JSON 응답"""
    try:
        cache_key = f"market_historical_data_1y"
        historical_data = cache.get(cache_key)

        if not historical_data:
            try:
                # 동기적으로 실행
                historical_data = collect_historical_data("1y")
            except Exception as e:
                logger.error(f"Failed to collect historical data: {e}")
                return JsonResponse(
                    {"error": "Failed to fetch historical data"}, status=500
                )

        formatted_data = []

        if chart_type == "indices":
            # 모든 날짜를 하나로 통합
            all_dates = sorted(
                set().union(
                    *[
                        historical_data[key].keys()
                        for key in ["sp500", "nasdaq", "kospi", "kosdaq"]
                        if key in historical_data
                    ]
                )
            )

            # 데이터 포맷팅
            for date in all_dates:
                data_point = {
                    "timestamp": date.isoformat(),
                    "sp500": historical_data["sp500"].get(date),
                    "nasdaq": historical_data["nasdaq"].get(date),
                    "kospi": historical_data["kospi"].get(date),
                    "kosdaq": historical_data["kosdaq"].get(date),
                }
                formatted_data.append(data_point)

        elif chart_type == "bonds":
            # 모든 날짜를 하나로 통합
            all_dates = sorted(
                set().union(
                    *[
                        historical_data[key].keys()
                        for key in ["us_10y", "us_3m", "us_30y", "us_spread"]
                        if key in historical_data
                    ]
                )
            )

            # 데이터 포맷팅
            for date in all_dates:
                data_point = {
                    "timestamp": date.isoformat(),
                    "us_10y": historical_data["us_10y"].get(date),
                    "us_3m": historical_data["us_3m"].get(date),
                    "us_30y": historical_data["us_30y"].get(date),
                    "us_spread": historical_data["us_spread"].get(date),
                }
                formatted_data.append(data_point)

        else:
            return JsonResponse({"error": "Invalid chart type"}, status=400)

        if not formatted_data:
            return JsonResponse({"error": "No data available"}, status=404)

        # 차트 데이터 캐시
        chart_cache_key = f"chart_data_{chart_type}"
        cache.set(chart_cache_key, formatted_data, 3600)

        return JsonResponse({"data": formatted_data})

    except Exception as e:
        import traceback

        logger.error(f"Error in get_chart_data: {str(e)}\n{traceback.format_exc()}")
        return JsonResponse({"error": f"Internal server error: {str(e)}"}, status=500)
