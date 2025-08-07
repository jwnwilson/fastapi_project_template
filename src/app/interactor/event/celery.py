from celery import Celery
from hexrepo_log import setup_logger
from hexrepo_task.interactor.event.celery import CeleryConfig, create_celery_app

from app.config import config

setup_logger()

celery_config = CeleryConfig(
    CELERY_BROKER_URL=config.CELERY_BROKER_URL,
    CELERY_RESULT_BACKEND=config.CELERY_RESULT_BACKEND,
    REGION=config.REGION,
)
celery_app: Celery = create_celery_app(celery_config)
