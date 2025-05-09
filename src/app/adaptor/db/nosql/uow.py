from logging import config
from hexrepo_db.nosql import BaseDynamoUOW
from .models.example import ExampleRepository
from app.config import config


class DynamoUOW(BaseDynamoUOW):
    # Used for testing
    def create_all(self) -> None:
        self.example.create_table()

    def drop_all(self) -> None:
        self.example.delete_table()

    @property
    def example(self) -> ExampleRepository:
        project: str = config.PROJECT
        table_name: str = "example"
        env: str = config.ENVIRONMENT
        full_table_name = f"{project}_{env}_{table_name}"
        return ExampleRepository(
            self.resource, table=full_table_name, required_filters=self._required_filters
        )