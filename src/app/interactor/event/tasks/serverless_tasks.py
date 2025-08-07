from hexrepo_task.interactor.event.app import Dependency

from app.adaptor.db.sql import SqlUOW
from app.domain.example import ExampleDTO

from ...dependencies import get_uow
from ..lambda_app import app


@app.task
def example_task(
    example: ExampleDTO, uow: SqlUOW = Dependency(get_uow)
):
    print(example)
