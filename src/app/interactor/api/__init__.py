{% if use_api_type == 'serverless' %}
from .lambda_wrapper import handler as lambda_handler  # noqa
{% endif %}
