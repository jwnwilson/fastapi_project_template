import logging

from hexrepo_log import log_manager, setup_logger

from .tasks.serverless_tasks import app


def handler(event, context):
    setup_logger()
    logging.getLogger("botocore").setLevel(logging.INFO)

    with log_manager():
        return app.handle(event)
