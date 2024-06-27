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
    article_id = serializers.CharField(required=False)
    ca_query = serializers.CharField(required=False)

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
                "package_id can only be integer"
            )
        return value
    
    def validate_article_id(self, value):
        if not valid_integer(value):
            raise serializers.ValidationError(
                "article_id can only be integer"
            )
        return value
    
    def to_internal_value(self, data):
        # data["ca_query"] = eval(data.get('ca_query',"False").title())
        if data["ca_query"]=="true":
            data["package_id"]=1
            data["class_id"]=1
            print("article_id",data.get("article_id"))
            if not data.get("article_id"):
                data["article_id"] = "abcd"
            
        return super().to_internal_value(data)



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




