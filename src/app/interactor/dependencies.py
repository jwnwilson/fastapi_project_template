import logging
import uuid
from collections.abc import Generator
from pydantic import BaseModel

from app.config import config
{% if use_task %}
from hexrepo_task import QueueAdaptor, SqsQueueAdaptor
from hexrepo_task.adaptor.db import QueueUOW
{% endif %}
{% if use_db %}
from hexrepo_db import UOW
{% endif %}
{% if use_db_logic == "sql" %}
from hexrepo_db.sql import get_sql_db_url
from app.adaptor.db.sql import SqlUOW
{% elif use_db and use_db_logic == "nosql" %}
from app.adaptor.db.nosql import DynamoUOW
{% else %}
from hexrepo_db import UOW, Repository
from hexrepo_db.sql.stub import StubbedRepository

from app.domain.example import ExampleDTO
{% endif %}

logger = logging.getLogger(__name__)


{% if use_db and use_db_logic == "sql" %}
def get_uow() -> Generator[UOW, None, None]:
    uow = SqlUOW(db_url=get_sql_db_url())
    with uow.transaction():
        yield uow
{% elif use_db and use_db_logic == "nosql" %}
def get_uow() -> Generator[UOW, None, None]:
    # Leave empty string to use aws env vars
    uow = DynamoUOW(db_url=config.DB_URL)
    yield uow
{% else %}
class StubbedExampleRepository(StubbedRepository):
    model_dto: ExampleDTO = ExampleDTO

    def _generate_fake_dto(self, obj_in: BaseModel = None) -> BaseModel:
        return self.model_dto(
            id=uuid.uuid4(),
            name="test",
            url="https://test.com",
            location="test location",
        )


class StubbedUOW(UOW):
    @property
    def example(self) -> Repository:
        return StubbedExampleRepository()


def get_uow() -> Generator[UOW, None, None]:
    yield StubbedUOW(db_url="test")
{% endif %}

{% if use_task %}
def get_queue_uow() -> Generator[UOW, None, None]:
    uow: UOW = QueueUOW()
    yield uow


def get_task_queue() -> Generator[QueueAdaptor, None, None]:
    queue = SqsQueueAdaptor(queue="hexrepo-tasks")
    yield queue
{% endif %}