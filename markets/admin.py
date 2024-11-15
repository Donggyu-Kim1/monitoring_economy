# markets/admin.py
from django.contrib import admin
from .models import (
    MarketIndex,
    BondYield,
    ExchangeRate,
    Commodity,
    EconomicCalendar,
    NewsHeadline,
)


@admin.register(MarketIndex)
class MarketIndexAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "sp500", "nasdaq", "kospi", "kosdaq", "vix", "dxy")
    list_filter = ("timestamp",)
    ordering = ("-timestamp",)


@admin.register(BondYield)
class BondYieldAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "us_10y", "us_2y", "us_spread")
    list_filter = ("timestamp",)
    ordering = ("-timestamp",)


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "usd_krw", "eur_usd", "jpy_krw")
    list_filter = ("timestamp",)
    ordering = ("-timestamp",)


@admin.register(Commodity)
class CommodityAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "gold", "wti", "bitcoin")
    list_filter = ("timestamp",)
    ordering = ("-timestamp",)


@admin.register(EconomicCalendar)
class EconomicCalendarAdmin(admin.ModelAdmin):
    list_display = (
        "indicator",
        "release_date",
        "frequency",
        "previous_value",
        "forecast_value",
        "actual_value",
        "is_released",
    )
    list_filter = ("indicator", "frequency", "is_released", "release_date")
    ordering = ("-release_date",)


@admin.register(NewsHeadline)
class NewsHeadlineAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "title", "source")
    list_filter = ("source", "timestamp")
    search_fields = ("title", "summary")
    ordering = ("-timestamp",)
