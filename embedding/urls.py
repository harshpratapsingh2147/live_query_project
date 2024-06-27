from django.urls import path, include
from rest_framework.routers import DefaultRouter
from embedding.views import CAEmbeddingsView

router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path(
        "ca", CAEmbeddingsView.as_view(), name="ca_embedding"
    ),
    
]