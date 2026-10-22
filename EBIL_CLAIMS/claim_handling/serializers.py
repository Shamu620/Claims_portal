from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers
from .models import Claim, MotorDetail, Non_MotorDetail, Credit_LifeDetail


class MotorDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotorDetail
        exclude = ('claim',)

class Non_MotorDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Non_MotorDetail
        exclude = ('claim',)

class Credit_LifeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Credit_LifeDetail
        exclude = ('claim',)

class ClaimMotorSerializer(serializers.ModelSerializer):
    motor_details = MotorDetailSerializer(required=True, partial=True)
    class Meta:
        model = Claim
        fields = '__all__'


    def create(self, validated_data):
        motor_data = validated_data.pop('motor_details', None)
        claim = Claim.objects.create(**validated_data)
        if motor_data:
            if motor_data.get('registration_number'):
                motor_data['registration_number'] = motor_data['registration_number'].upper()
            MotorDetail.objects.create(claim=claim, **motor_data)
        return claim

    def update(self, instance, validated_data):
        motor_data = validated_data.pop('motor_details', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if motor_data:
            detail_instance, _ = MotorDetail.objects.get_or_create(claim=instance) #get_or_create returns a tuple: (object, created(True-if none existed, False-if existed).
            for key, value in motor_data.items(): #In Python, .items() is a built-in method used on dictionaries. It extracts all the key-value pairs from the dictionary so you can iterate (loop) through them together.
                setattr(detail_instance, key, value)
            detail_instance.save()
        return instance

 #=======================


# def update(self, instance, validated_data):
#     credit_life_data = validated_data.pop('credit_life_details', None)
#     # Update Claim fields
#     for key, value in validated_data.items():
#         setattr(instance, key, value)
#     instance.save()
#     # Update nested Credit_LifeDetail partially
#     if credit_life_data:
#         detail_instance, _ = Credit_LifeDetail.objects.get_or_create(claim=instance) 👉 get_or_create always returns two things:1.The object itself (detail_instance), 2. A boolean (created) that says whether it was newly made (True) or just fetched (False). 👉 In your code, you’re only keeping the object (detail_instance) and ignoring the boolean (that’s why _ is used).
#         for key, value in credit_life_data.items():
#             setattr(detail_instance, key, value)
#         detail_instance.save()
#     return instance
#=======================
#=======================OR=========================================================
    # def update(self, instance, validated_data):
    #     motor_data = validated_data.pop('motor_details', None)
    #     # Update the Claim fields
    #     instance = super().update(instance, validated_data)
    #     # Update or create the related MotorDetail
    #     if motor_data:
    #         MotorDetail.objects.update_or_create(
    #             claim=instance, defaults=motor_data)
    #     return instance

class ClaimNon_MotorSerializer(serializers.ModelSerializer):
    non_motor_details = Non_MotorDetailSerializer(required=True, partial=True)
    class Meta:
        model = Claim
        fields = '__all__'

    def create(self, validated_data):
        non_motor_data = validated_data.pop('non_motor_details', None)
        claim = Claim.objects.create(**validated_data)
        if non_motor_data:
            Non_MotorDetail.objects.create(claim=claim, **non_motor_data)
        return claim

    def update(self, instance, validated_data):
        non_motor_data = validated_data.pop('non_motor_details', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if non_motor_data:
            detail_instance, _ = Non_MotorDetail.objects.get_or_create(claim=instance)
            for key, value in non_motor_data.items():
                setattr(detail_instance, key, value)
        return instance

class ClaimCredit_LifeSerializer(serializers.ModelSerializer):
    credit_life_details = Credit_LifeDetailSerializer(required=True, partial=True)
    class Meta:
        model = Claim
        fields = '__all__'

    def create(self, validated_data):
        credit_life_data = validated_data.pop('credit_life_details', None)
        claim = Claim.objects.create(**validated_data)
        if credit_life_data:
            Credit_LifeDetail.objects.create(claim=claim, **credit_life_data)
        return claim

    def update(self, instance, validated_data):
        credit_life_data = validated_data.pop('credit_life_details', None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if credit_life_data:
            detail_instance, _ = Credit_LifeDetail.objects.get_or_create(claim=instance)
            for key, value in credit_life_data.items():
                setattr(detail_instance, key, value)
            detail_instance.save()
        return instance

    # def update(self, instance, validated_data):
    #     credit_life_data = validated_data.pop('credit_life_details', None)
    #     for key, value in validated_data.items():
    #         setattr(instance, key, value)
    #     instance.save()
    #     if credit_life_data:
             #Credit_LifeDetail.objects.update_or_create(claim=instance, defaults=credit_life_data)




    #
    # def create(self, validated_data):
    #     more_user_details = validated_data.pop('more_user_details', None)
    #     if validated_data['username']:
    #         validated_data.pop('username')
    #     validated_data['username'] = f"{validated_data['first_name'][0] if validated_data['first_name'] else ""}+{validated_data['last_name'][0] if validated_data['last_name'] else ""}+{more_user_details['pf'] if validated_data['pf'] else ""}"
    #     user_data=User.objects.create_user(**validated_data)
    #     if more_user_details is not None:
    #         MoreUserDetails.objects.create(details = user_data, **more_user_details)
    #     return f"Successfully made {validated_data['first_name'] if validated_data['first_name'] else ""} + {validated_data['last_name'] if validated_data['last_name'] else ""} as {validated_data['username'] if validated_data['username'] else ""}" #DO not return the validated data as it contains hardcoded data
    #
    # def update(self, instance, validated_data):
    #     more_user_details = validated_data.pop('more_user_details', None)
    #     for key, value in validated_data.items():
    #         setattr(instance, key, value)
    #         instance.save()
    #     if more_user_details is not None:
    #         detail_instance, _ = MoreUserDetails.objects.get_or_create(details=instance)
    #         for key, value in more_user_details.items():
    #             setattr(detail_instance, key, value)
    #         detail_instance.save()
    #     return f"Successfully updated {validated_data['first_name'] if validated_data['first_name'] else ""} + {validated_data['last_name'] if validated_data['last_name'] else ""}"
