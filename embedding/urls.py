from django.urls import path, include
from rest_framework.routers import DefaultRouter
from embedding.views import CAEmbeddingsView, CAPDFEmbeddingsView

router = DefaultRouter()

urlpatterns = [
    path("", include(router.urls)),
    path(
        "ca", CAEmbeddingsView.as_view(), name="ca_embedding"
    ),
    path(
        "ca/pdf", CAPDFEmbeddingsView.as_view(), name="ca_pdf"
    ),
    
]