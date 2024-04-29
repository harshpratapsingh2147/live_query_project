from rest_framework.generics import GenericAPIView
#from .utility import question_answer
from .gpt_utility import question_answer
from .validate_serializer import LiveQueryValidateSerializer
from rest_framework.response import Response
# Create your views here.


class LiveQuestionAnswer(GenericAPIView):
    validate_serializer_class = LiveQueryValidateSerializer

    def get(self, request):
        filter_serializer = self.validate_serializer_class(data=request.GET)
        class_id = request.GET.get('class_id')
        query = request.GET.get('query')
        member_id = request.GET.get('member_id')
        refresh = request.GET.get('refresh')
        package_id = request.GET.get('package_id')

        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors)

        result = question_answer(
            class_id=class_id,
            member_id=member_id,
            query=query,
            refresh=refresh,
            package_id=package_id
        )

        res = {
            query: result
        }
        return Response(res)



