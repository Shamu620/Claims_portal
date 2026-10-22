import json
import random
from typing import Any

from django.contrib import messages
from django.contrib.auth import logout, authenticate, login, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from rest_framework import status
from rest_framework.response import Response

from user_accounts import serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import BasePermission, IsAuthenticated

from user_accounts.models import Otp



# ==========ROLE-BASED-AUTHENTICATION===================
# For django native authentication
def is_admin(user: Any):
    return bool(
        getattr(user, 'is_authenticated',
                False) and  # protection against AttributeError if the user doesn't have 'is_authentacted details
        getattr(user, 'more_user_details',
                None) and  # protection against Attribute error if the user doesn't have more_user_details attribute
        user.more_user_details.role == 'Admin'
    )


# for rest APIs
class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'more_user_details', None) and
            request.user.more_user_details.role == 'Admin'
        )

# def test_email_view(request):
#     try:
#         send_mail(
#             subject='Test OTP from Claims Portal',
#             message='This is a test email to confirm Brevo SMTP is working correctly!',
#             from_email=None,  # Automatically uses your DEFAULT_FROM_EMAIL setting
#             recipient_list=['shalommumo620@gmail.com'],  # Replace with any email you want to receive it
#             fail_silently=False,
#         )
#         return HttpResponse("Email sent successfully! Check your inbox.")
#     except Exception as e:
#         return HttpResponse(f"Failed to send email: {str(e)}")

@require_http_methods(['GET', 'POST'])
def recover_password_send_otp(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email_input = data.get('email')
        except json.JSONDecodeError:
            email_input = None

        try:
            user = User.objects.get(email__iexact=email_input)
        except User.DoesNotExist:
            return JsonResponse({
                "error": f"The email {email_input or ''} was not found in our servers! Kindly try again using a valid email"
            }, status=400)

        if user:
            user_email = user.email
            try:
                initial_user_otp_instances = Otp.objects.filter(email__iexact=user_email)
                initial_user_otp_instances.delete()
            except user.DoesNotExist:
                pass

            otp = random.randint(100000, 999999)
            otp_instance = Otp.objects.create(
                email=user_email,
                otp=otp
            )
            otp_instance.save()

            try:
                send_mail(
                    subject="Claims Portal Password Recovery",
                    message=f"""
                                Hello {user.first_name},
                                Your one-time password (OTP) is {otp}.
                                This code will expire in 10 minutes. Please do not share this code with anyone.
                                If you did not request this, please ignore this email.

                                Best regards,
                                Claims Portal Support
                                """,
                    from_email=None,  # Automatically uses your DEFAULT_FROM_EMAIL setting
                    recipient_list=[user_email],
                    fail_silently=False

                )
                return JsonResponse({
                    "success": f"Sucessfully sent emails to {user_email}"
                }, status=200)
            except Exception as e:
                return JsonResponse({
                    "Error": f"Failed to send the email:: {str(e)}"
                }, status=500)

    return render(request, 'forgot_password_page.html')


@require_POST
def recover_password_confirm_otp(request):
    try:
        data = json.loads(request.body)
        otp_input = data.get('verification_code')
        email = data.get('email')
    except json.JSONDecodeError:
        otp_input = None

    if otp_input:
        user_otp_instance = Otp.objects.get(email__iexact=email)
        correct_otp = user_otp_instance.otp
        if otp_input == correct_otp:
            ASCII_CHARS = [
                '!', '#', '$', '%', '&', '(', ')', '*', '+', ',', '-', '.', '/',
                '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?',
                '@', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O',
                'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', '^', '_',
                'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
                'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '|'
            ]
            temporary_password = ''.join(random.choices(ASCII_CHARS, k=8))
            user = User.objects.get(email__iexact=email)
            user.set_password(temporary_password)
            user.last_login = None
            user.save(update_fields=['password', 'last_login'])
            send_mail(
                subject="Your Temporary Claims Portal Password",
                message=f"""
                        Hello {user.first_name},
                        We received a request to reset the password for your Claims portal account.
                        Your temporary password is: {temporary_password}
                        For security purposes, this password is valid for the next 24 hours only.
                        Please log in to your account and update your password immediately by following these steps:
                        1. Go to the [Claims Portal Log In Page].
                        2. Log in using your email address and the temporary password provided above.
                        3. Follow the on-screen prompts to set a new, secure password.
                        If you did not request this password reset, please disregard this email and **immediately**
                        contact our support team immediately to secure your account.

                        Best regards,
                        Claims Portal Support
                        """,
                from_email=None,  # Automatically uses your DEFAULT_FROM_EMAIL setting
                recipient_list=[email],
                fail_silently=False
            )
            user_otp_instance.delete()  # delete the otp

            return JsonResponse({
                "success": f"Successfully sent email to {email}"
            }, status=200)
        else:
            user_otp_instance.delete()
            return JsonResponse({
                "error": "The verification code you provided is invalid or has expired! Kindly repeat the process or contact the claims portal support"
            }, status=400)
    else:

        return JsonResponse({
            "error": "No verification code provided/reached the server!"
        }, status=405)


# def is_admin(user):
#     return bool(user.is_authenticated and user.more_user_details.role == 'Admin')



# ==================PAGES=========================
# ================================================
# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def create_user(request):
#     serializer = serializers.UserDetailsSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return JsonResponse(serializer.data, status=201, safe=False)
#     return JsonResponse(serializer.errors, status = 405, safe=False)

@require_POST
@login_required(login_url='login_page')
def get_user_name_initials(request):
    user = request.user
    first_name_inital = user.first_name[0] if user.first_name else "-"
    last_name_initial = user.last_name[0] if user.last_name else "-"
    name_initials = f"{first_name_inital}{last_name_initial}"
    role = user.more_user_details.role
    return JsonResponse({
        "name_initials": name_initials,
        "role": role
    }, status=200)


@require_GET
@login_required(login_url='login_page')
@user_passes_test(is_admin)
def user_management_page(request):
    user = request.user

    # Safely grab the first letter if it exists, otherwise use an empty string
    first_initial = user.first_name[0] if user.first_name else ""
    last_initial = user.last_name[0] if user.last_name else ""

    # Combine them, convert to uppercase, or fallback to "U" if both are blank
    name_initials = f"{first_initial}{last_initial}".upper() or "U"
    try:
        role = user.more_user_details.role
    except (ObjectDoesNotExist, AttributeError):
        role = 'User'

    context = {
        "role": role,
        "name_initials": name_initials
    }

    return render(request, 'user_management.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminRole])
@user_passes_test(is_admin)
def fetch_all_users(request):
    users_data = User.objects.values('id', 'first_name', 'last_name', 'email',
                                     'more_user_details__pf', 'username', 'more_user_details__role', 'date_joined',
                                     'last_login')
    data = []

    for user in users_data:
        data.append({
            "user_id": user['id'],
            # "first_name": user['first_name'],
            # "last_name": user['last_name'],
            "name": user['first_name'] + " " + user['last_name'],
            "pf": user['more_user_details__pf'],
            "username": user['username'],
            "email": user['email'],
            "role": user['more_user_details__role'],
            "date_joined": user['date_joined'].strftime('%d/%m/%Y') if user['date_joined'] else "",
            "last_login": "Never Logged in" if user['last_login'] is None else user['last_login'].strftime(
                "%d/%m/%Y - %I:%M %p"),
        })

    admins = User.objects.filter(more_user_details__role='Admin').count()
    sub_admins = User.objects.filter(more_user_details__role='Sub-Admin').count()
    total_users = admins + sub_admins

    count_info = ({
        "admins_count": admins,
        "sub_admins_count": sub_admins,
        "total_users": total_users,
    })

    context = ({
        "data": data,
        "count_info": count_info,
    })

    return JsonResponse(context, safe=False)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated, IsAdminRole])
def create_user(request):
    # if request.method == "GET":
    #     return JsonResponse({
    #         "info": "Enter the details of the user"
    #     })
    serializer = serializers.UserDetailsSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)  # 400 with the errors
    user = serializer.save()
    return JsonResponse(
        {'message': f"Successfully made {user.first_name} {user.last_name} as {user.username}"},
        status=201,
    )


# @api_view(['POST'])
# # @permission_classes([IsAuthenticated, IsAdminRole])
# def create_users_bulk(request):
#     # Check if the incoming request data is a list (bulk payload)
#     if not isinstance(request.data, list):
#         return Response(
#             {"error": "Expected a list of user objects in the payload."},
#             status=status.HTTP_400_BAD_REQUEST
#         )
#
#     # Pass many=True to let DRF handle a list of objects
#     serializer = serializers.UserDetailsSerializer(data=request.data, many=True)
#
#     if serializer.is_valid():
#         # This will save all 30 users (and triggers your atomic transaction logic)
#         users = serializer.save()
#         return Response({
#             "success": True,
#             "message": f"Successfully created {len(users)} users in bulk!",
#             "usernames": [user.username for user in users]
#         }, status=status.HTTP_201_CREATED)
#
#     # If any user in the batch fails validation, return 400 with errors
#     return Response({
#         "error": "Bulk creation failed due to validation errors.",
#         "details": serializer.errors
#     }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PATCH'])
@permission_classes([IsAuthenticated, IsAdminRole])
def update_user(request, user_id):
    if request.method == "GET":
        return JsonResponse({
            "info": "Enter the details of the user to update"
        })
    user = get_object_or_404(User, pk=user_id)
    serializer = serializers.UserDetailsSerializer(user, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    return JsonResponse(
        {'message': f"Successfully updated {user.first_name} {user.last_name}"},
        status=200,
    )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsAdminRole])
def delete_user(request, user_id, pf):
    try:
        user = User.objects.get(pk=user_id, more_user_details__pf=pf)
        user.delete()
        return JsonResponse({
            "success": f"successful deleted {user.first_name} {user.last_name}"
        }, status=200)
    except Exception as e:
        return JsonResponse({
            "error": str(e)
        }, status=405)


@require_POST  # Recommended for security to prevent CSRF logout attacks via simple links
@login_required(login_url='login_page')
def logout_view(request):
    logout(request)
    return redirect('login_page')


@never_cache  # To ensure never serve a cached login page (cause the CSRF token of that page will be outdated)
@ensure_csrf_cookie
@require_http_methods(['GET', 'POST'])
def login_page(request):
    if request.method == "POST":
        user_input = request.POST.get('user_input')
        password_input = request.POST.get('password')
        try:
            if '@' in user_input:
                user = User.objects.get(email__iexact=user_input)
                username = user.username
            else:
                user = User.objects.get(username__iexact=user_input)
                username = user.username
        except User.DoesNotExist:
            username = user_input
        except User.MultipleObjectsReturned:
            # Fallback if multiple users share the same email/username
            user = User.objects.filter(email__iexact=user_input).first()
            if user:
                username = user.username
            else:
                username = user_input

        user = authenticate(request, username=username, password=password_input)

        # check whether the user is new (to force password change)
        try:
            new_user = User.objects.get(last_login__isnull=True, username=username)
        except:
            new_user = None

        if new_user:
            if user is not None:
                login(request, user)
                return redirect('first_time_password_change')
            else:
                messages.error(request, "Invalid Username or Password")

        else:
            if user is not None:
                login(request, user)
                return redirect('pending_claims_page')
            else:
                messages.error(request, "Invalid Username or Password")
    return render(request, 'login_page.html')


@require_http_methods(['GET', 'POST'])
@login_required(login_url='login_page')
def first_time_password_change(request):
    if request.method == "POST":
        new_password = request.POST.get('new_password')
        user = User.objects.get(username=request.user.username)
        user.set_password(new_password)
        user.save(update_fields=['password'])
        # CRITICAL: Keep the user logged in with the updated session hash
        update_session_auth_hash(request, user)

        first_initial = user.first_name[0].upper() if user.first_name else ""
        last_initial = user.last_name[0].upper() if user.last_name else ""
        name_initials = f"{first_initial}{last_initial}" or "-"
        context = {
            "name_initials": name_initials,
            "username": user.username,
            "first_name": user.first_name
        }
        return render(request, 'successful_password_change.html', context=context)
    else:
        user = request.user
        # Safely handle empty first/last names to prevent IndexError
        first_initial = user.first_name[0].upper() if user.first_name else ""
        last_initial = user.last_name[0].upper() if user.last_name else ""
        name_initials = f"{first_initial}{last_initial}" or "-"
        context = {
            "name_initials": name_initials,
            "username": user.username,
            "first_name": user.first_name
        }

        return render(request, 'first_time_password_change.html', context=context)


@require_http_methods(['GET', 'POST'])
@login_required(login_url='login_page')
def change_password(request):
    if request.method == "POST":
        user = request.user
        input_current_password = request.POST.get('old_password')
        current_password = user.password
        input_new_password = request.POST.get('new_password')
        if check_password(input_current_password, current_password):
            user.set_password(input_new_password)
            user.save(update_fields=['password'])
            # CRITICAL: Keep the user logged in with the updated session hash
            update_session_auth_hash(request, user)

            first_initial = user.first_name[0].upper() if user.first_name else ""
            last_initial = user.last_name[0].upper() if user.last_name else ""
            name_initials = f"{first_initial}{last_initial}" or "-"
            context = {
                "name_initials": name_initials,
                "username": user.username,
                "first_name": user.first_name
            }
            return render(request, 'successful_password_change.html', context=context)
        else:
            # Safely handle empty first/last names to prevent IndexError
            first_initial = user.first_name[0].upper() if user.first_name else ""
            last_initial = user.last_name[0].upper() if user.last_name else ""
            name_initials = f"{first_initial}{last_initial}" or "-"
            context = {
                "name_initials": name_initials,
                "username": user.username,
                "first_name": user.first_name
            }
            return render(request, 'incorrect_current_password.html', context=context)

    user = request.user
    # Safely handle empty first/last names to prevent IndexError
    first_initial = user.first_name[0].upper() if user.first_name else ""
    last_initial = user.last_name[0].upper() if user.last_name else ""
    name_initials = f"{first_initial}{last_initial}" or "-"
    context = {
        "name_initials": name_initials,
        "username": user.username,
        "first_name": user.first_name
    }
    return render(request, "change_password.html", context=context)


@require_GET
def admin_contacts_page(request):
    return render(request, 'admin_contacts_page.html')
