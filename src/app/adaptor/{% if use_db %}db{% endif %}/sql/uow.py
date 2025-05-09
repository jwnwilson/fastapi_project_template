from hexrepo_db.sql import BaseSqlUOW
from .models.example import ExampleRepository

class SqlUOW(BaseSqlUOW):

    @property
    def example(self) -> ExampleRepository:
        return ExampleRepository(self.session)