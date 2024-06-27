import logging
import os


from django.db.models import Q, F
from django.utils.decorators import method_decorator
from django.conf import settings

from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from exceptions.exceptions import (
    ExtendedValidationError,
    ExtendedParseError
)

from core.utility import CommonService
from core.enums import ErrorMessages
from embedding.validate_serializer import CaEmbeddingValidateSerializer
from embedding.utility import process_embeddings


logger = logging.getLogger()


class CAEmbeddingsView(GenericAPIView):
    """
    It is used to list open job details.
    """
    
    validate_serializer_class = CaEmbeddingValidateSerializer

    
    def post(self, request):
        # validate input data
        # import pdb;pdb.set_trace()
        filter_serializer = self.validate_serializer_class(data=request.data, many=True)
        if not filter_serializer.is_valid():
            err_msg = filter_serializer.errors
            logger.warning({"error": err_msg})
            print(err_msg)
            raise ExtendedValidationError(
                detail=err_msg,
                msg="Invalid Request Parameters",
                # request_id=request.request_id,
            )
        
        # add the word in db
        data = filter_serializer.validated_data
        _status, msg  = process_embeddings(data)
        
        if not _status:
            raise ExtendedParseError(
                msg=ErrorMessages.EMBEDDING_PROCESS_FAILURE.value.format(reason=msg),
            )
            
        result = CommonService.add_fields(
                message=msg
            )
        data = CommonService.default_response(result, True, "Success")
        return Response(data)


