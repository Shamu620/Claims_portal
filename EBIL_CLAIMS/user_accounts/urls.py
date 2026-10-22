from django.urls import path

from user_accounts import views

urlpatterns = [

#===================AUTHENTICATION PAGEs======================
path('user-management/', views.user_management_page, name='user_management_page'),
path('admin-contacts-page/', views.admin_contacts_page, name='admin_contacts_page'),
path('recover-password/', views.recover_password_send_otp, name='forgot_password_page'),


#====================AUTHENTICATION APIs=====================
path('api/create-user/', views.create_user, name='create_user'),
path('api/update-user/<int:user_id>/', views.update_user, name='update_user'),
path('api/delete-user/<int:user_id>/<str:pf>/', views.delete_user, name='delete_user'),
path('api/fetch-all-users/', views.fetch_all_users, name='fetch_all_users'),
path('api/get-user-name-initials/', views.get_user_name_initials, name='get_user_name_initials'),
path('first-time-password-change/', views.first_time_password_change, name='first_time_password_change'),
path('change-password/', views.change_password, name='change_password'),
path('api/confirm-otp/', views.recover_password_confirm_otp, name='api_confirm_otp'),

#======CREATE USERS IN BULK==========================
# path('api/create-users-in-bulk/', views.create_users_bulk, name='create_users_in_bulk'),

]



