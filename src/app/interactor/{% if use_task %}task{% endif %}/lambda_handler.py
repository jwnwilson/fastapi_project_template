from hexrepo_log import log_manager, setup_logger

from .tasks.app import app


def handler(event, context):
    setup_logger()

    with log_manager():
        return app.handle(event)
