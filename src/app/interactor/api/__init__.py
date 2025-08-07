{% if use_api_framework == 'fastapi' %}
from .lambda_wrapper import handler as lambda_handler  # noqa
{% endif %}
