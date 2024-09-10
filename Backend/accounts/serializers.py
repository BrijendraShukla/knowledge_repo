from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):

    full_name = serializers.SerializerMethodField('get_full_name')

    def get_full_name(self, obj):
        return obj.first_name + " " + obj.last_name

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name']
