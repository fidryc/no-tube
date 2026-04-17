from taskiq import TaskiqScheduler

from app.tasks.broker import broker
from taskiq.schedule_sources import LabelScheduleSource


scheduler = TaskiqScheduler(
    broker=broker,
    sources=[LabelScheduleSource(broker)],
)