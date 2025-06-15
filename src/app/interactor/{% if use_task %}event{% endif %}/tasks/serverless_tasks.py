from hexrepo_task.interactor.event.app import Dependency

from app.adaptor.db.sql import SqlUOW
from app.domain.user import UserPermissionCreateDTO

from ...dependencies import get_uow
from ..lambda_app import app


@app.task
def create_example_task_serverless(
    user_dto: UserPermissionCreateDTO, uow: SqlUOW = Dependency(get_uow)
):
    uow.user.create(user_dto)
