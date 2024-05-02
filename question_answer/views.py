from rest_framework.generics import GenericAPIView
#from .utility import question_answer
from question_answer.utility.gpt_utility import question_answer
from .validate_serializer import LiveQueryValidateSerializer, LikeDislikeSerializer, ChatHistorySerializer
from question_answer.utility.db_operations_utility import update_like_dislike_status, get_chat_history_for_ask_expert
from rest_framework.response import Response
# Create your views here.


class LiveQuestionAnswer(GenericAPIView):
    validate_serializer_class = LiveQueryValidateSerializer

    def get(self, request):
        filter_serializer = self.validate_serializer_class(data=request.GET)
        class_id = request.GET.get('class_id')
        query = request.GET.get('query')
        member_id = request.GET.get('member_id')
        old_conversation = request.GET.get('old_conversation')
        package_id = request.GET.get('package_id')

        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors)

        res, unique_id = question_answer(
            class_id=class_id,
            member_id=member_id,
            query=query,
            old_conversation=old_conversation,
            package_id=package_id
        )

        response = {
            query: res,
            "unique_id": unique_id,
        }

        return Response(response)


class LikeDislike(GenericAPIView):
    validate_serializer_class = LikeDislikeSerializer

    def put(self, request):
        filter_serializer = self.validate_serializer_class(data=request.data)

        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors)

        action = request.data.get('action')
        unique_id = request.data.get('unique_id')

        splits_of_uid = unique_id.split('_')
        id = splits_of_uid[0]
        time_stamp = splits_of_uid[1]

        if update_like_dislike_status(action=action, id=id, time_stamp=time_stamp):
            return Response("like status updated successfully")
        else:
            return Response("could not update status")


class ChatHistory(GenericAPIView):
    validate_serializer_class = ChatHistorySerializer

    def get(self, request):
        filter_serializer = self.validate_serializer_class(data=request.GET)

        if not filter_serializer.is_valid():
            return Response(filter_serializer.errors)

        class_id = request.GET.get('class_id')
        member_id = request.GET.get('member_id')

        chat_list = get_chat_history_for_ask_expert(
            class_id=class_id,
            member_id=member_id
        )

        print(chat_list)

        return Response(chat_list)


















