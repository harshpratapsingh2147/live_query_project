from rest_framework import serializers

from core.utility import Validators
from core.enums import ErrorMessages


class CaEmbeddingValidateSerializer(serializers.Serializer):
    id=serializers.IntegerField()
    title = serializers.CharField()
    content = serializers.CharField()
    published_date = serializers.CharField()
    url = serializers.CharField(required=False)
     
    # def validate_id(self, value):
    #     # to check if the id is numeric
    #     if not Validators.valid_list_of_integers(value):
    #         raise serializers.ValidationError(ErrorMessages.ID_INVALID.value)
    #     return value
        