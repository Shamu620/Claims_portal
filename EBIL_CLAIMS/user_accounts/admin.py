# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from .models import CustomUser
#
# @admin.register(CustomUser)
# class CustomUserAdmin(UserAdmin):
#     list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'branch', 'must_change_password', 'is_active')
#     list_filter = ('role', 'branch', 'must_change_password', 'is_active', 'is_staff')
#     search_fields = ('username', 'email', 'first_name', 'last_name')
#
#     fieldsets = UserAdmin.fieldsets + (
#         ('EBIL Info', {
#             'fields': ('role', 'branch', 'phone_number', 'must_change_password'),
#         }),
#     )
#     add_fieldsets = UserAdmin.add_fieldsets + (
#         ('EBIL Info', {
#             'fields': ('role', 'branch', 'phone_number', 'must_change_password'),
#         }),
#     )
#
#
#
#
#
#
#
#
