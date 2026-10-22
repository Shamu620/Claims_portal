# from django.contrib import admin
# from .models import Claim, MotorDetail
#
#
# class MotorDetailInline(admin.StackedInline):
#     """Allows viewing and editing MotorDetail directly inside the Claim admin page."""
#
#     model = MotorDetail
#     can_delete = False
#     verbose_name_plural = 'Motor Details'
#
#
# @admin.register(Claim)
# class ClaimAdmin(admin.ModelAdmin):
#     # Columns displayed in the list view table
#     list_display = (
#         'id',
#         'category',
#         'name_of_insured',
#         'intimation_date',
#         'date_of_loss',
#         'closure_date',
#         'tat_days',
#         'documented',
#     )
#
#     # Clickable links to open the detail view
#     list_display_links = ('id', 'name_of_insured')
#
#     # Sidebar filter options
#     list_filter = (
#         'category',
#         'documented',
#         'intimation_date',
#         'closure_date',
#         'tat',
#     )
#
#     # Search bar fields
#     search_fields = ('id', 'name_of_insured')
#
#     # # Calculated or non-editable fields
#     # readonly_fields = ('tat_days',)
#
#     # Navigation drill-down by date at the top of the table
#     date_hierarchy = 'intimation_date'
#
#     # Default ordering (newest intimation_date first)
#     ordering = ('-intimation_date',)
#
#     # Embedded forms for related models
#     inlines = [MotorDetailInline]