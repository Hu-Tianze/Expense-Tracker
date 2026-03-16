import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger(__name__)


def _extract_message(data):
    if isinstance(data, dict):
        if "detail" in data:
            return str(data["detail"])
        first_key = next(iter(data.keys()), None)
        if first_key is not None:
            value = data[first_key]
            if isinstance(value, list) and value:
                return f"{first_key}: {value[0]}"
            return f"{first_key}: {value}"
    return "Request failed"


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        logger.exception("Unhandled DRF exception", exc_info=exc)
        return Response(
            {
                "status": "error",
                "code": "internal_error",
                "message": "Internal server error",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    message = _extract_message(response.data)
    code = getattr(exc, "default_code", "request_error")
    if response.status_code == 401:
        code = "unauthenticated"
    elif response.status_code == 403:
        code = "permission_denied"
    elif response.status_code == 404:
        code = "not_found"
    elif response.status_code == 405:
        code = "method_not_allowed"

    response.data = {
        "status": "error",
        "code": str(code),
        "message": message,
    }
    return response
