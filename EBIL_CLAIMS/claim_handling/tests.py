from django.test import TestCase

# Create your tests here.

from claim_handling import models

underwriters = models.Claim.objects.values_list('underwriter', flat=True)

for underwriter in underwriters:
    print(underwriter)