from django.db import migrations
from django.db.models import F
from django.db.models.functions import ExtractDay
from django.utils import timezone


def populate_days_pending(apps, schema_editor):
    Claim = apps.get_model('claim_handling', 'Claim')
    Claim.objects.filter(status='Pending', days_pending__isnull=True).update(
        days_pending=ExtractDay(timezone.now().date() - F('intimation_date'))
    )


def reverse_populate_days_pending(apps, schema_editor):
    Claim = apps.get_model('claim_handling', 'Claim')
    Claim.objects.all().update(days_pending=None)


class Migration(migrations.Migration):

    dependencies = [
        ('claim_handling', '0007_add_claim_search_indexes_trimmed'),
    ]

    operations = [
        migrations.RunPython(populate_days_pending, reverse_populate_days_pending),
    ]