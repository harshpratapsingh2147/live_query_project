from rest_framework import serializers


def valid_integer(value):
    if not value.isdigit():
        return False
    return True


class LiveQueryValidateSerializer(serializers.Serializer):
    class_id = serializers.CharField(required=True)
    query = serializers.CharField(required=True)
    member_id = serializers.CharField(required=True)
    refresh = serializers.CharField(required=True)
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

    def validate_refresh(self, value):
        if not valid_integer(value) and value not in [0, 1]:
            raise serializers.ValidationError(
                "refresh can only be 0 or 1"
            )
        return value

    def validate_package_id(self, value):
        if not valid_integer(value):
            raise serializers.ValidationError(
                "member_id can only be integer"
            )
        return value

