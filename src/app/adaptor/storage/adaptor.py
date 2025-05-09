from hexrepo_cloud.storage import S3Adaptor, StorageConfig
from app.config import config


def get_storage(
        bucket: str = f"{config.PROJECT}-{config.ENVIRONMENT}-example",
        region: str = config.REGION,
    ) -> S3Adaptor:
    storage_config: StorageConfig = StorageConfig(
        aws_bucket=bucket,
        aws_region=region
    )
    return S3Adaptor(storage_config=storage_config)
