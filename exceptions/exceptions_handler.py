from rest_framework.views import exception_handler

from exceptions.error_message import ErrorMessage
from django.http import JsonResponse


def custom_exception_handler(exc, context):
    handlers = {
        "ExtendedPermissionDenied": _handle_permission_denied_error,
        "ExtendedParseError": _handle_generic_error,
        "ExtendedValidationError": _handle_validation_error,
        "ExtendedAuthenticationFailed": _handle_authentication_error,
        "ExtendedNotAuthenticated": _handle_authentication_error,
        "ExtendedNotFound": _handle_generic_error,
        "ExtendedNoContentException": _handle_generic_error,
        "ExtendedInternalServer": _handle_generic_error,
    }
    response = exception_handler(exc, context)
    exception_class = exc.__class__.__name__
    if exception_class in handlers:
        return handlers[exception_class](exc, context, response)
    return response


def _handle_validation_error(exc, context, response):
    error = ErrorMessage.error_response(exc, context)
    response.data.clear()
    response.data.update(error)
    return response


def _handle_permission_denied_error(exc, context, response):
    error = ErrorMessage.error_response(exc, context)
    del response.data["detail"]
    response.data.update(error)
    return response


def _handle_generic_error(exc, context, response):
    error = ErrorMessage.error_response(exc, context)
    del response.data["detail"]
    response.data.update(error)
    return response


def _handle_authentication_error(exc, context, response):
    error = ErrorMessage.error_response(exc, context)
    del response.data["detail"]
    response.data.update(error)
    return response


def handle_not_found_error(request, exception=None):
    return JsonResponse(ErrorMessage.error_404_response(request=request), status=404)
