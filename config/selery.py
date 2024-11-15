from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "market_monitor.settings")

app = Celery("market_monitor")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "collect-market-data-daily": {
        "task": "markets.tasks.collect_all_market_data",
        "schedule": crontab(hour=18, minute=0),  # 매일 오후 6시
    },
    "collect-news-hourly": {
        "task": "markets.tasks.collect_news",
        "schedule": crontab(minute=0),  # 매시 정각
    },
    "update-economic-calendar": {
        "task": "markets.tasks.update_economic_calendar",
        "schedule": crontab(hour="9-17", minute="*/30"),  # 장중 30분마다
    },
}
