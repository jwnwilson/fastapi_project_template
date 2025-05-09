from hexrepo_api.lambda_wrapper import create_lambda_handler


from .fastapi.main import app  # noqa


handler = create_lambda_handler(app)
