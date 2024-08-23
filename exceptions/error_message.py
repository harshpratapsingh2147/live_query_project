from exceptions.exceptions import ExtendedValidationError
from django.utils import timezone


class ErrorMessage:
    @staticmethod
    def default_error_response(err, status_code):
        err_response = {}
        err_responses = []
        msg = ""
        error_dict = err.detail
        for key, value in error_dict.items():
            if key == "msg":
                msg = value
            else:
                err_response[key] = value
        err_responses.append(err_response)
        return err_responses, msg

    @staticmethod
    def error_response(errors, context):
        output = {"result": None}
        response = {}
        error_dict = errors.__dict__
        details = error_dict.get("detail")

        for key, value in error_dict.items():
            if key == "detail":
                if isinstance(errors, ExtendedValidationError):
                    response["details"] = {
                        sub_key: sub_value[0] for sub_key, sub_value in details.items()
                    }
            if key == "msg":
                response["msg"] = value if value is not None else errors.default_detail
            else:
                response[key] = value

        response.pop("detail")
        response["status_code"] = errors.status_code
        response["status_text"] = errors.default_code
        response["path"] = context.get("request").build_absolute_uri()
        output["response"] = response
        return output

    @staticmethod
    def error_404_response(request):
        output = {"result": None}
        response = dict()
        response["msg"] = "Page Not Found"
        response["status_code"] = 404
        response["status_text"] = "Not Found"
        response["path"] = request.build_absolute_uri()
        response["request_id"] = request.request_id
        response["timestamp"] = timezone.now()
        output["response"] = response
        return output
