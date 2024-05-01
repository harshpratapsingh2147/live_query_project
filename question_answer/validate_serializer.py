from rest_framework import serializers
import re

class UniqueIDValidator:
    def __call__(self, value):
        pattern = re.compile(r'^\d+_\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d+$')
        if not pattern.match(value):
            raise serializers.ValidationError("Invalid unique_id format")


def valid_integer(value):
    if not value.isdigit():
        return False
    return True


class LiveQueryValidateSerializer(serializers.Serializer):
    class_id = serializers.CharField(required=True)
    query = serializers.CharField(required=True)
    member_id = serializers.CharField(required=True)
    old_conversation = serializers.CharField(required=True)
    package_id = serializers.CharField(required=True)

    def validate_class_id(self, value):
        if not valid_integer(value):
            raise serializers.ValidationError(
                "class_id can only be integer"
            )
        return value

    def validate_member_id(self, value):
        if not valid_integer(value):
            raise serializers.ValidationError(
                "member_id can only be integer"
            )
        return value

    def validate_old_conversation(self, value):
        if value not in ['true', 'false']:
            raise serializers.ValidationError(
                "old_conversation can only be true or false"
            )
        return value

    def validate_package_id(self, value):
        if not valid_integer(value):
            raise serializers.ValidationError(
                "member_id can only be integer"
            )
        return value


class LikeDislikeSerializer(serializers.Serializer):
    action = serializers.CharField(required=True)
    unique_id = serializers.CharField(validators=[UniqueIDValidator()], required=True)

    def validate_action(self, value):
        if value not in ['0', '1', '2']:
            raise serializers.ValidationError(
                "action can only be 0, 1, 2"
            )
        return value


class ChatHistorySerializer(serializers.Serializer):
    class_id = serializers.CharField(required=True)
    member_id = serializers.CharField(required=True)

    def validate_class_id(self, value):
        if not valid_integer(value):
            raise serializers.ValidationError(
                "class_id can only be integer"
            )
        return value

    def validate_member_id(self, value):
        if not valid_integer(value):
            raise serializers.ValidationError(
                "member_id can only be integer"
            )
        return value




