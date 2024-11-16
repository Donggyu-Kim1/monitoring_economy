from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timedelta
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from .models import (
    MarketIndex,
    BondYield,
    ExchangeRate,
    Commodity,
    EconomicCalendar,
    NewsHeadline,
)
import logging

logger = logging.getLogger(__name__)


@shared_task
def collect_market_indices():
    """주식 시장 지수 데이터 수집"""
    try:
        indices = {
            "sp500": "^GSPC",
            "nasdaq": "^IXIC",
            "kospi": "^KS11",
            "kosdaq": "^KQ11",
            "vix": "^VIX",
            "dxy": "DX-Y.NYB",
        }

        data = {}
        for name, ticker in indices.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d")
                if not hist.empty:
                    data[name] = hist["Close"][-1]
            except Exception as e:
                logger.error(f"Error fetching {name}: {e}")
                data[name] = None

        MarketIndex.objects.create(**data)
        logger.info("Market indices collected successfully")
        return "Market indices collection completed"
    except Exception as e:
        logger.error(f"Failed to collect market indices: {e}")
        raise


@shared_task
def collect_bond_yields():
    """채권 수익률 데이터 수집"""
    try:
        bonds = {"us_10y": "^TNX", "us_3m": "^IRX", "us_30y": "^TYX"}

        data = {}
        for name, ticker in bonds.items():
            try:
                bond = yf.Ticker(ticker)
                hist = bond.history(period="1d")
                if not hist.empty:
                    data[name] = hist["Close"][-1]
            except Exception as e:
                logger.error(f"Error fetching {name}: {e}")
                data[name] = None

        # Calculate spread
        if data.get("us_30y") and data.get("us_3m"):
            data["us_spread"] = data["us_30y"] - data["us_3m"]

        BondYield.objects.create(**data)
        logger.info("Bond yields collected successfully")
        return "Bond yields collection completed"
    except Exception as e:
        logger.error(f"Failed to collect bond yields: {e}")
        raise


@shared_task
def collect_exchange_rates():
    """환율 데이터 수집"""
    try:
        pairs = {"usd_krw": "KRW=X", "eur_usd": "EURUSD=X", "jpy_krw": "JPYKRW=X"}

        data = {}
        for name, ticker in pairs.items():
            try:
                forex = yf.Ticker(ticker)
                hist = forex.history(period="1d")
                if not hist.empty:
                    data[name] = hist["Close"][-1]
            except Exception as e:
                logger.error(f"Error fetching {name}: {e}")
                data[name] = None

        ExchangeRate.objects.create(**data)
        logger.info("Exchange rates collected successfully")
        return "Exchange rates collection completed"
    except Exception as e:
        logger.error(f"Failed to collect exchange rates: {e}")
        raise


@shared_task
def collect_commodities():
    """원자재 가격 데이터 수집"""
    try:
        commodities = {"gold": "GC=F", "wti": "CL=F", "bitcoin": "BTC-USD"}

        data = {}
        for name, ticker in commodities.items():
            try:
                commodity = yf.Ticker(ticker)
                hist = commodity.history(period="1d")
                if not hist.empty:
                    data[name] = hist["Close"][-1]
            except Exception as e:
                logger.error(f"Error fetching {name}: {e}")
                data[name] = None

        Commodity.objects.create(**data)
        logger.info("Commodities collected successfully")
        return "Commodities collection completed"
    except Exception as e:
        logger.error(f"Failed to collect commodities: {e}")
        raise


@shared_task
def collect_historical_data(period="1y"):
    """1년치 과거 데이터 수집"""
    try:
        # 티커 심볼 매핑
        indices = {
            "sp500": "^GSPC",
            "nasdaq": "^IXIC",
            "kospi": "^KS11",
            "kosdaq": "^KQ11",
            "vix": "^VIX",
            "dxy": "DX-Y.NYB",
        }
        bonds = {"us_10y": "^TNX", "us_3m": "^IRX", "us_30y": "^TYX"}
        exchange_rates = {
            "usd_krw": "KRW=X",
            "eur_usd": "EURUSD=X",
            "jpy_krw": "JPYKRW=X",
        }
        commodities = {"gold": "GC=F", "wti": "CL=F", "bitcoin": "BTC-USD"}

        historical_data = {}

        # 지수 데이터 수집
        for name, ticker in indices.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=period)
                if not hist.empty:
                    historical_data[name] = hist["Close"].to_dict()
            except Exception as e:
                logger.error(f"Error fetching historical data for {name}: {e}")

        # 채권 데이터 수집
        for name, ticker in bonds.items():
            try:
                bond = yf.Ticker(ticker)
                hist = bond.history(period=period)
                if not hist.empty:
                    historical_data[name] = hist["Close"].to_dict()
            except Exception as e:
                logger.error(f"Error fetching historical data for {name}: {e}")

        # 스프레드 계산
        if "us_30y" in historical_data and "us_3m" in historical_data:
            historical_data["us_spread"] = {}
            for date in historical_data["us_30y"].keys():
                if date in historical_data["us_3m"]:
                    historical_data["us_spread"][date] = (
                        historical_data["us_30y"][date] - historical_data["us_3m"][date]
                    )

        # 환율 데이터 수집
        for name, ticker in exchange_rates.items():
            try:
                forex = yf.Ticker(ticker)
                hist = forex.history(period=period)
                if not hist.empty:
                    historical_data[name] = hist["Close"].to_dict()
            except Exception as e:
                logger.error(f"Error fetching historical data for {name}: {e}")

        # 원자재 데이터 수집
        for name, ticker in commodities.items():
            try:
                commodity = yf.Ticker(ticker)
                hist = commodity.history(period=period)
                if not hist.empty:
                    historical_data[name] = hist["Close"].to_dict()
            except Exception as e:
                logger.error(f"Error fetching historical data for {name}: {e}")

        # Redis에 데이터 캐싱
        cache_key = f"market_historical_data_{period}"
        cache.set(cache_key, historical_data, timeout=3600)  # 1시간 캐시

        logger.info(f"Historical data collected successfully for period: {period}")
        return historical_data

    except Exception as e:
        logger.error(f"Failed to collect historical data: {e}")
        raise


@shared_task
def collect_news():
    """뉴스 헤드라인 수집"""
    try:
        # Yahoo Finance 뉴스
        url = "https://finance.yahoo.com/news"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        headlines = []
        for article in soup.find_all("h3", limit=10):  # 상위 10개 뉴스
            try:
                title = article.text.strip()
                link = article.find_parent("a")["href"]
                if not link.startswith("http"):
                    link = "https://finance.yahoo.com" + link

                headlines.append(
                    {"title": title, "source": "Yahoo Finance", "url": link}
                )
            except Exception as e:
                logger.error(f"Error parsing news article: {e}")

        # 기존 뉴스 삭제 (최근 50개만 유지)
        NewsHeadline.objects.all()[50:].delete()

        # 새 뉴스 저장
        for headline in headlines:
            NewsHeadline.objects.create(**headline)

        logger.info("News headlines collected successfully")
        return "News collection completed"
    except Exception as e:
        logger.error(f"Failed to collect news: {e}")
        raise


@shared_task
def update_economic_calendar():
    """경제 지표 발표 일정 업데이트"""
    try:
        # 오늘 발표 예정인 지표들 확인
        today = datetime.now().date()
        indicators = EconomicCalendar.objects.filter(
            release_date=today, is_released=False
        )

        for indicator in indicators:
            try:
                # 실제 값 수집 로직 (API나 웹 스크래핑으로 구현)
                # 예시 코드:
                actual_value = get_indicator_value(indicator.indicator)
                if actual_value is not None:
                    indicator.actual_value = actual_value
                    indicator.is_released = True
                    indicator.save()
            except Exception as e:
                logger.error(f"Error updating indicator {indicator.indicator}: {e}")

        logger.info("Economic calendar updated successfully")
        return "Economic calendar update completed"
    except Exception as e:
        logger.error(f"Failed to update economic calendar: {e}")
        raise


def get_indicator_value(indicator_name):
    """경제 지표 값 수집 (실제 구현 필요)"""
    # 여기에 실제 데이터 수집 로직 구현
    pass


@shared_task
def collect_all_market_data():
    """모든 시장 데이터 수집 태스크"""
    try:
        # 모든 수집 태스크 실행
        collect_market_indices.delay()
        collect_bond_yields.delay()
        collect_exchange_rates.delay()
        collect_commodities.delay()
        collect_news.delay()
        update_economic_calendar.delay()
        collect_historical_data.delay()

        logger.info("All market data collection tasks initiated")
        return "All collection tasks started"
    except Exception as e:
        logger.error(f"Failed to initiate market data collection: {e}")
        raise
