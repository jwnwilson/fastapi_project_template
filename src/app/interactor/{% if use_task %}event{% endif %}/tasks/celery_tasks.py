from hexrepo_task.interactor.event.app import Dependency, resolve_dependencies

from app.adaptor.db.sql import SqlUOW
from app.domain.example import ExampleDTO

from ...dependencies import get_uow
from ..celery import celery_app


@celery_app.task
def test_task():
    print("test task")


@celery_app.task
@resolve_dependencies
def create_example_task(
    example: ExampleDTO, uow: SqlUOW = Dependency(get_uow)
):
    print(example)
