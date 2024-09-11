from rest_framework import serializers
import re
from question_answer.utility.db_operations_utility import get_new_chat_session_id


class UniqueIDValidator:
    def __call__(self, value):
        pattern = re.compile(r"^\d+_\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}.\d+$")
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
    section = serializers.CharField(required=True)
    article_id = serializers.CharField(required=False)
    chat_session_id = serializers.CharField(required=False)
    ca_query = serializers.CharField(required=False)

    def validate_class_id(self, value):
        if not valid_integer(value):
            raise serializers.ValidationError("class_id can only be integer")
        return value

    def validate_member_id(self, value):
        if not valid_integer(value):
            raise serializers.ValidationError("member_id can only be integer")
        return value

    def validate_old_conversation(self, value):
        if value not in ["true", "false"]:
            raise serializers.ValidationError(
                "old_conversation can only be true or false"
            )
        return value

    def validate_package_id(self, value):
        if not valid_integer(value):
            raise serializers.ValidationError("package_id can only be integer")
        return value

    def validate_article_id(self, value):
        val = value.split(",")
        for item in val:
            if not valid_integer(item):
                raise serializers.ValidationError("article_id can only be integer")
        return value

    def validate_chat_session_id(self, value):
        if not valid_integer(value):
            raise serializers.ValidationError("chat_session_id can only be integer")
        return value

    def to_internal_value(self, data):
        # data["ca_query"] = eval(data.get('ca_query',"False").title())
        if data.get("ca_query") == "true":
            data["package_id"] = 1
            data["class_id"] = 1
            data["section"] = 1
            print("article_id", data.get("article_id"))
            if not data.get("article_id"):
                if (not data.get("chat_session_id")) and (
                    data.get("old_conversation") == "true"
                ):
                    data["chat_session_id"] = "abcd"
                elif (not data.get("chat_session_id")) and (
                    data.get("old_conversation") == "false"
                ):
                    data["chat_session_id"] = get_new_chat_session_id(data.get("member_id"))
            # else:
                # data["article_id"] = "abcd"

        return super().to_internal_value(data)


class LikeDislikeSerializer(serializers.Serializer):
    action = serializers.CharField(required=True)
    unique_id = serializers.CharField(validators=[UniqueIDValidator()], required=True)

    def validate_action(self, value):
        if value not in ["0", "1", "2"]:
            raise serializers.ValidationError("action can only be 0, 1, 2")
        return value


class ChatHistorySerializer(serializers.Serializer):
    class_id = serializers.CharField(required=True)
    member_id = serializers.CharField(required=True)

    def validate_class_id(self, value):
        if not valid_integer(value):
            raise serializers.ValidationError("class_id can only be integer")
        return value

    def validate_member_id(self, value):
        if not valid_integer(value):
            raise serializers.ValidationError("member_id can only be integer")
        return value


class PredictQuestionsSerializer(serializers.Serializer):
    chat_id = serializers.CharField(required=True)
    article_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    def validate_chat_id(self, value):
        if not valid_integer(value):
            raise serializers.ValidationError("chat_id can only be integer")
        return value

    def validate_article_id(self, value):
        print("article_id:", value)
        value_list = value.strip().split(",")
        for val in value_list:
            if not valid_integer(val):
                raise serializers.ValidationError("article_id can only be integer")
        return  value
