from hexrepo_log import setup_logger

setup_logger()

from app.adaptor.db.nosql.uow import DynamoUOW
from app.config import config


def create_dynamodb_tables():
    uow = DynamoUOW(db_url=config.DB_URL)
    uow.create_all()


if __name__ == "__main__":
    create_dynamodb_tables()