# markets/models.py
from django.db import models
from django.utils import timezone


class MarketIndex(models.Model):
    """주식 시장 지수 모델"""

    timestamp = models.DateTimeField(default=timezone.now)
    sp500 = models.FloatField(verbose_name="S&P 500", null=True)
    nasdaq = models.FloatField(verbose_name="NASDAQ", null=True)
    kospi = models.FloatField(verbose_name="KOSPI", null=True)
    kosdaq = models.FloatField(verbose_name="KOSDAQ", null=True)
    vix = models.FloatField(verbose_name="VIX", null=True)
    dxy = models.FloatField(verbose_name="Dollar Index", null=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "시장 지수"
        verbose_name_plural = "시장 지수들"

    def __str__(self):
        return f"Market Indices - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class BondYield(models.Model):
    """채권 수익률 모델"""

    timestamp = models.DateTimeField(default=timezone.now)
    us_10y = models.FloatField(verbose_name="US 10Y", null=True)
    us_2y = models.FloatField(verbose_name="US 2Y", null=True)
    us_spread = models.FloatField(verbose_name="2s10s Spread", null=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "채권 수익률"
        verbose_name_plural = "채권 수익률들"

    def __str__(self):
        return f"Bond Yields - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class ExchangeRate(models.Model):
    """환율 모델"""

    timestamp = models.DateTimeField(default=timezone.now)
    usd_krw = models.FloatField(verbose_name="USD/KRW", null=True)
    eur_usd = models.FloatField(verbose_name="EUR/USD", null=True)
    jpy_krw = models.FloatField(verbose_name="JPY/KRW", null=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "환율"
        verbose_name_plural = "환율들"

    def __str__(self):
        return f"Exchange Rates - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class Commodity(models.Model):
    """원자재 가격 모델"""

    timestamp = models.DateTimeField(default=timezone.now)
    gold = models.FloatField(verbose_name="Gold", null=True)
    wti = models.FloatField(verbose_name="WTI", null=True)
    bitcoin = models.FloatField(verbose_name="Bitcoin", null=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "원자재"
        verbose_name_plural = "원자재들"

    def __str__(self):
        return f"Commodities - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class EconomicCalendar(models.Model):
    """경제 지표 발표 일정 모델"""

    FREQUENCY_CHOICES = [
        ("monthly", "월간"),
        ("quarterly", "분기"),
        ("annual", "연간"),
    ]

    INDICATOR_CHOICES = [
        ("cpi", "CPI"),
        ("pce", "PCE"),
        ("gdp", "GDP"),
        ("unemployment", "실업률"),
        ("pmi", "PMI"),
    ]

    indicator = models.CharField(
        max_length=20, choices=INDICATOR_CHOICES, verbose_name="경제지표"
    )
    release_date = models.DateField(verbose_name="발표일")
    frequency = models.CharField(
        max_length=10, choices=FREQUENCY_CHOICES, verbose_name="발표주기"
    )
    previous_value = models.FloatField(verbose_name="이전 값", null=True)
    forecast_value = models.FloatField(verbose_name="예상 값", null=True)
    actual_value = models.FloatField(verbose_name="실제 값", null=True)
    is_released = models.BooleanField(default=False, verbose_name="발표 여부")

    class Meta:
        ordering = ["-release_date"]
        verbose_name = "경제 지표"
        verbose_name_plural = "경제 지표들"

    def __str__(self):
        return f"{self.get_indicator_display()} - {self.release_date}"


class NewsHeadline(models.Model):
    """뉴스 헤드라인 모델"""

    timestamp = models.DateTimeField(default=timezone.now)
    title = models.CharField(max_length=500, verbose_name="제목")
    source = models.CharField(max_length=100, verbose_name="출처")
    url = models.URLField(verbose_name="링크")
    summary = models.TextField(verbose_name="요약", null=True, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "뉴스"
        verbose_name_plural = "뉴스들"

    def __str__(self):
        return f"{self.title[:50]}... - {self.source}"
