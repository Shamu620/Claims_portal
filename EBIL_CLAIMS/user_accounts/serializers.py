from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from user_accounts.models import MoreUserDetails


class MoreUserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoreUserDetails
        fields = ['role', 'pf']
        extra_kwargs = {'pf': {'validators': []}}  # uniqueness checked in the parent serializer

class UserDetailsSerializer(serializers.ModelSerializer):
    more_user_details = MoreUserDetailsSerializer(required=True)
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'password', 'more_user_details']
        read_only_fields = ['id', 'username']
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False},
        }

    def validate_more_user_details(self, value):
        pf = value.get('pf')
        if pf:
            qs = MoreUserDetails.objects.filter(pf=pf)
            if self.instance is not None:
                qs = qs.exclude(details=self.instance)
            if qs.exists():
                raise ValidationError({'pf': 'A user with this PF already exists.'})
        return value

    @staticmethod
    def _build_username(first_name, last_name, pf):
        return f"{first_name[0]}{last_name[0]}{pf}"

    @transaction.atomic
    def create(self, validated_data):
        more_user_details = validated_data.pop('more_user_details')
        validated_data['username'] = self._build_username(
            validated_data['first_name'],
            validated_data['last_name'],
            more_user_details['pf'],
        )
        user = User.objects.create_user(**validated_data)  # hashes the password
        MoreUserDetails.objects.create(details=user, **more_user_details)
        return user

    @transaction.atomic
    def update(self, instance, validated_data):
        more_user_details = validated_data.pop('more_user_details', None)
        password = validated_data.pop('password', None)

        for key, value in validated_data.items():
            setattr(instance, key, value)
        if password:
            instance.set_password(password)

        details = getattr(instance, 'more_user_details', None)
        if more_user_details:
            if details is None:
                details = MoreUserDetails.objects.create(details=instance, **more_user_details)
            else:
                for key, value in more_user_details.items():
                    setattr(details, key, value)
                details.save()

        if details is not None:
            instance.username = self._build_username(
                instance.first_name, instance.last_name, details.pf
            )
        instance.save()
        return instance
