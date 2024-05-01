
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LiveQuestionAnswer, LikeDislike, ChatHistory

router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path(
        "query", LiveQuestionAnswer.as_view(), name="live_question_answer"
    ),
    path(
        "like", LikeDislike.as_view(), name="like_dislike"
    ),
    path(
        "chat-history", ChatHistory.as_view(), name="chat_history"
    )
]