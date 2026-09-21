from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response

    detail = response.data.get("detail") if isinstance(response.data, dict) else None
    if detail:
        message = str(detail)
    else:
        message = "Request failed."

    response.data = {
        "status": "error",
        "message": message,
        "data": response.data,
    }
    return response
