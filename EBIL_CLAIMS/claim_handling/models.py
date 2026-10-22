from django.contrib.auth import password_validation
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from mypy_django_plugin.lib.fullnames import ONETOONE_FIELD_FULLNAME
from rest_framework.fields import CharField
from django.db.models import GeneratedField
from django.db.models.functions import Now
from datetime import timedelta  # not needed here
from datetime import date
from django.db import models
from django.db.models import Case, When, Value, F, IntegerField
from django.db.models.functions import ExtractDay, Now, Cast
from django.db.models import DateField
from django.db import models
from django.db.models import Case, When, Value, IntegerField, F, DateField
from django.db.models.functions import Now, ExtractDay, Cast

from .validations import validate_supporting_documents, validate_supporting_images, validate_time
from datetime import datetime
# Create your models here.

CATEGORY_CHOICES = [
    ('Motor', 'Motor'),
    ('Non_Motor', 'Non Motor'),
    ('Credit_Life', 'Credit Life'),
]

class ClaimQuerySet(models.QuerySet):
    def with_days_pending(self):
        return self.annotate(
            days_pending=Case(
                When(
                    status='Pending',
                    intimation_date__isnull=False,
                    then=ExtractDay(
                        Cast(Now(), output_field=DateField()) - F('intimation_date')
                    ),
                ),
                default=Value(None),
                output_field=IntegerField(),
            )
        )

class ClaimManager(models.Manager.from_queryset(ClaimQuerySet)):
    pass

class Claim(models.Model):
    id = models.AutoField(primary_key=True,)
    category = models.CharField(null=False, blank=False, choices=CATEGORY_CHOICES, max_length=15)
    intimation_date = models.DateField(null=False, blank=False, validators=[validate_time])
    name_of_insured = models.CharField(null=False, blank=False, max_length=50, db_index=True)
    date_of_loss = models.DateField(null=False, blank=False, validators=[validate_time])
    documented = models.BooleanField(null=False, blank=False, default=False)
    date_fully_documented = models.DateField(null=True, blank=True, validators=[validate_time])
    underwriter = models.CharField(max_length=50, null=False, blank=False, db_index=True)
    branch = models.CharField(max_length=50, null=False, blank=False, db_index=True)
    handler = models.CharField(max_length=50, null=False, blank=False, db_index=True)
    status = models.CharField(max_length=50, null=False, blank=False, db_index=True)
    sub_status = models.CharField(max_length=50, db_index=True, null=True, blank=True)
    notes = models.TextField(null=True, blank=True, default='')
    closure_date = models.DateField(null=True, blank=True, validators=[validate_time])
    tat_cl = models.IntegerField(null=True, blank=True)
    tat_dv = models.IntegerField(null=True, blank=True)

    circumstance = models.CharField(max_length=50,  null=False, blank=False, default="Testing ENV") #cause of event in credit_life
    sum_insured = models.DecimalField(max_digits=15, decimal_places=2, null=True, default=0.00) # Loan amount for credit_life
    date_dv_issued = models.DateField(null=True, blank=True, validators=[validate_time])
    dv_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, default=0.00)
    date_dv_returned = models.DateField(null=True, blank=True, validators=[validate_time])
    amount_paid = models.DecimalField(max_digits=15, decimal_places=2, null=True, default=0.00)

    # days_pending = models.GeneratedField(
    #     expression=Case(
    #         When(
    #             status='Pending',
    #             intimation_date__isnull=False,
    #             then=ExtractDay(
    #                 Cast(Now(), output_field=DateField()) - F('intimation_date')
    #             ),
    #         ),
    #         default=Value(None),
    #         output_field=IntegerField(),
    #     ),
    #     output_field=IntegerField(),
    #     db_persist=False,  # virtual column
    # )
    # supporting_documents = models.FileField(upload_to='media/supporting_documents/',
    #                                         null=True, blank=True,
    #                                         validators= [validate_supporting_documents])
    # supporting_images = models.ImageField(upload_to='media/supporting_images/',
    #                                       null=True, blank=True,
    #                                       validators=[validate_supporting_images])
    created_at = models.DateTimeField(auto_now_add=True, null=False, blank=False, validators=[validate_time])
    updated_at = models.DateTimeField(auto_now=True, null=False, blank=False, validators=[validate_time])



    objects = ClaimManager()

    def save(self, *args, **kwargs):
        if self.closure_date and self.intimation_date:
            self.tat_cl = (self.closure_date - self.intimation_date).days
        if self.date_dv_issued and self.intimation_date:
            self.tat_dv = (self.date_dv_issued - self.intimation_date).days
        super().save(*args, **kwargs)


class MotorDetail(models.Model):
    claim = models.OneToOneField(Claim, on_delete=models.CASCADE,
                                 related_name='motor_details', primary_key=True)
    registration_number = models.CharField(max_length=15, null=False, blank=False, db_index=True)
    motor_class = models.CharField(max_length=50, null=False, blank=False)
    assessor = models.CharField(max_length=50, null=True, blank=True, db_index=True,)
    # circumstance = models.CharField(max_length=50,  null=False, blank=False)
    # sum_insured = models.DecimalField(max_digits=15, decimal_places=2, null=True, default=0.00)
    # date_dv_issued = models.DateField(null=True, blank=True, validators=[validate_time])
    # dv_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, default=0.00)
    # date_dv_returned = models.DateField(null=True, blank=True, validators=[validate_time])
    # amount_paid = pass

class Non_MotorDetail(models.Model):
    claim = models.OneToOneField(Claim, on_delete=models.CASCADE,
                                 primary_key=True, related_name= 'non_motor_details')
    cover_type = models.CharField(max_length=50, null=False, blank=False)
    # circumstance = models.CharField(max_length=50, null=False, blank=False)
    # sum_insured = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=0.00)
    # amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=0.00)

class Credit_LifeDetail(models.Model):
    claim = models.OneToOneField(Claim, on_delete=models.CASCADE, primary_key=True,
                                 related_name='credit_life_details')
    claim_trigger = models.CharField(max_length=50, null=False, blank=False,)
    # event_date = models.DateField(null=False, blank=False, validators=[validate_time])
    # cause_of_event/circumstance = models.CharField(max_length=15, null=False, blank=False,)
    # loan_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, default=0.00)
    # amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, default=0.00)
























