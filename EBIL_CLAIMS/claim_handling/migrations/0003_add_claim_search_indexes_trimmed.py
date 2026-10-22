"""
claims/migrations/0003_add_claim_search_indexes.py

CORRECTED VERSION:
  - Dependency now points to the actual prior migration filename.
  - Trigram index now targets `name_of_insured` (the real field name),
    not `client` (which was a guess based on the UI column label).
  - branch, handler, category already have db_index=True (confirmed from
    0002_alter_claim_branch_alter_claim_handler_and_more.py), so no
    redundant AddIndex calls for those.

Run with: python manage.py migrate
"""

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("claim_handling", "0002_alter_claim_branch_alter_claim_handler_and_more"),
    ]

    operations = [
        # One-time extension enable. On Supabase this is usually already
        # available — check Database > Extensions in the dashboard first;
        # if it's already on, this operation is a harmless no-op.
        TrigramExtension(),

        migrations.AddIndex(
            model_name="claim", #Case Insensitive
            index=GinIndex(
                fields=["name_of_insured"],
                name="claim_insured_trgm_idx",
                opclasses=["gin_trgm_ops"],
            ),
        ),
    ]