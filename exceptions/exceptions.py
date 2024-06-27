from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import (
    ParseError,
    PermissionDenied,
    ValidationError,
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    APIException
)


class ExtendedNoContentException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "No Content"
    default_code = "No Content"

    def __init__(self, detail=None, msg=None, code=None, request_id=None):
        super().__init__(detail=detail, code=code)
        self.msg = msg
        self.timestamp = timezone.now()
        self.request_id = request_id


class ExtendedParseError(ParseError):
    def __init__(self, detail=None, msg=None, code=None, request_id=None):
        super().__init__(detail=detail, code=code)
        self.msg = msg
        self.timestamp = timezone.now()
        self.request_id = request_id


class ExtendedPermissionDenied(PermissionDenied):
    def __init__(self, detail=None, msg=None, code=None, request_id=None):
        super().__init__(detail=detail, code=code)
        self.msg = msg
        self.timestamp = timezone.now()
        self.request_id = request_id


class ExtendedValidationError(ValidationError):
    def __init__(self, detail=None, msg=None, code=None, request_id=None):
        super().__init__(detail=detail, code=code)
        self.msg = msg
        self.timestamp = timezone.now()
        self.request_id = request_id


class ExtendedAuthenticationFailed(AuthenticationFailed):
    def __init__(self, detail=None, msg=None, code=None, request_id=None):
        super().__init__(detail=detail, code=code)
        self.msg = msg
        self.timestamp = timezone.now()
        self.request_id = request_id


class ExtendedNotAuthenticated(NotAuthenticated):
    def __init__(self, detail=None, msg=None, code=None, request_id=None):
        super().__init__(detail=detail, code=code)
        self.msg = msg
        self.timestamp = timezone.now()
        self.request_id = request_id


class ExtendedNotFound(NotFound):
    def __init__(self, detail=None, msg=None, code=None, request_id=None):
        super().__init__(detail=detail, code=code)
        self.msg = msg
        self.timestamp = timezone.now()
        self.request_id = request_id


class ExtendedInternalServer(APIException):
    def __init__(self, detail=None, msg=None, code=None, request_id=None):
        super().__init__(detail=detail, code=code)
        self.msg = msg
        self.timestamp = timezone.now()
        self.request_id = request_id
