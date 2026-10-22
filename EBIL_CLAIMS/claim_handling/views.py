import csv
import random
from datetime import datetime
import io
import time
from multiprocessing import context
import io
import csv
from typing import Any

import xlsxwriter
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.http import HttpResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.permissions import IsAuthenticated, BasePermission

from user_accounts.models import Otp
from .models import Claim

from django.contrib.auth import password_validation, authenticate, login, logout, update_session_auth_hash
from django.db.models import Q, FloatField, Model
from django.db.models.functions import TruncMonth, ExtractDay, Cast

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import safestring
from openpyxl import Workbook
from rest_framework import status, request, response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
# from rest_framework.utils import timezone

from . import serializers
from .serializers import ClaimMotorSerializer, ClaimNon_MotorSerializer, ClaimCredit_LifeSerializer
from .models import Claim
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.db.models import Avg, Count, Q, F






@login_required(login_url='login_page')
@require_http_methods(['GET'])
def all_pending_claims_page(request):
    return render(request, 'all_pending_claims.html')

@login_required(login_url='login_page')
@require_http_methods(['GET'])
def motor_claims_pending_page(request):
    return render(request, 'motor_claims.html')

@login_required(login_url='login_page')
@require_http_methods(['GET'])
def non_motor_claims_pending_page(request):
    return render(request, 'non_motor_claims.html')

@login_required(login_url='login_page')
@require_http_methods(['GET'])
def credit_life_claims_pending_page(request):
    return render(request, 'credit_life_claims.html')

@login_required(login_url='login_page')
@require_http_methods(['GET'])
def legal_claims_page(request):
    return render(request, 'legal_claims.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reports_underwriter_performance_page(request):

    # Executes EXACTLY ONE SQL query across the entire database table
    underwriter_metrics = Claim.objects.values('underwriter').annotate(
        total_claims=Count('id'),
        closed_claims=Count('id', filter=Q(status='Closed')),
        pending_claims=Count('id', filter=Q(status='Pending')),
        paid_claims=Count('id', filter=Q(sub_status='Paid')),
        rejected_claims=Count('id', filter=Q(sub_status='Rejected')),
        avg_tat=Avg('tat_dv', filter=Q(status='Closed'))
    )

    underwriter_data = []
    total_claims_all = 0
    total_closed_claims = 0
    total_pending_claims = 0 #to be used in calculation of overall settlement ratio
    total_paid_claims = 0
    number_of_all_underwriters = 0
    turnaround_time_sum = 0

    for row in underwriter_metrics:
        total_claims_per_underwriter = row['total_claims'] or 0.0
        total_closed_claims_per_underwriter = row['closed_claims'] or 0.0
        total_pending_claims_per_underwriter = row['pending_claims'] or 0.0
        turnaround_time = row['avg_tat'] or 0.0
        paid_claims = row['paid_claims']


        total_claims_all += total_claims_per_underwriter
        total_closed_claims += total_closed_claims_per_underwriter
        total_pending_claims += total_pending_claims_per_underwriter
        number_of_all_underwriters += 1
        turnaround_time_sum += turnaround_time
        total_paid_claims += paid_claims

        underwriter_data.append({
            'underwriter_name': row['underwriter'],
            'total_claims_per_underwriter': total_claims_per_underwriter,
            'closed_claims': total_closed_claims_per_underwriter,
            'pending_claims': total_pending_claims_per_underwriter,
            'settlement_ratio': round((paid_claims / total_closed_claims_per_underwriter) * 100, 2) if row['paid_claims'] > 0 and total_closed_claims_per_underwriter > 0 else 0.0,
            'average_tat_dv': round(turnaround_time, 1) if turnaround_time is not None else 0.0,
            'rejection_rate': round((row['rejected_claims'] / total_claims_per_underwriter) * 100, 2) if total_claims_per_underwriter > 0 else 0.0,

        })

    # Sort underwriter_data by total_claims in descending order
    sorted_underwriter_data = sorted(
        underwriter_data,
        key=lambda x: x['settlement_ratio'],
        reverse=True
    )

    if number_of_all_underwriters > 0:
        overall_settlement_ratio = round((total_paid_claims / total_claims_all) * 100, 2)
        average_turnaround_time_all = round((turnaround_time_sum / number_of_all_underwriters), 2)

    else:
        overall_settlement_ratio = 0
        average_turnaround_time_all = 0



    underwriter_metrics={
        'total_claims_all': total_claims_all,
        'total_closed_claims_all': total_closed_claims,
        'total_pending_claims_all': total_pending_claims,
        'overall_settlement_ratio': overall_settlement_ratio,
        'average_turnaround_time_all': average_turnaround_time_all,
    }

    context = {
        "underwriter_data": sorted_underwriter_data,
        "underwriter_metrics": underwriter_metrics
    }

    return render(request, 'reports_underwriter_performance.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reports_claims_data_page(request):

    return render(request, 'reports_claims_data_page.html')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def reports_trends_page(request):
    lodged_by_month = Claim.objects.filter(intimation_date__year=2026).annotate(
        month=TruncMonth('intimation_date')
    ).values('month').annotate(lodged_per_month=Count('id')).order_by('month')

    closed_by_month = Claim.objects.filter(closure_date__year=2026).annotate(
        month=TruncMonth('closure_date')
    ).values('month').annotate(closed_per_month=Count('id')).order_by('month')

    combined_lodged_closed_trend = {}

    for row in lodged_by_month:
        combined_lodged_closed_trend[row['month']] = {'lodged': row['lodged_per_month'], 'closed': 0}
    for row in closed_by_month:
        combined_lodged_closed_trend.setdefault(row['month'], {'lodged': 0, 'closed': 0})
        combined_lodged_closed_trend[row['month']]['closed'] = row['closed_per_month']

    final_combined_lodged_closed_trend = [{
        'month': month.strftime('%b'),
        'lodged': v['lodged'],
        'closed': v['closed']
    } for month, v in combined_lodged_closed_trend.items()]

    settlement_ratio_per_underwriter = Claim.objects.filter(closure_date__year=2026, status='Closed').annotate(
        month=TruncMonth('closure_date')).values('month', 'underwriter').annotate(
        paid_claims=Count('id', filter=Q(sub_status='Paid')),
        closed_claims=Count('id')
    ).annotate(settlement_ratio=Cast('paid_claims', FloatField()) / F('closed_claims') * 100).order_by('month',
                                                                                                       'underwriter')

    underwriters_all_occurences = []

    for item in settlement_ratio_per_underwriter:
        underwriters_all_occurences.append(item["underwriter"])

    all_underwriters = set(underwriters_all_occurences)

    each_underwriter_data = []

    for underwriter in all_underwriters:
        each_underwriter_data.append({"underwriter": underwriter, "data": {}})

    for underwriter in each_underwriter_data:
        for row in settlement_ratio_per_underwriter:
            if row["underwriter"] == underwriter["underwriter"]:
                underwriter["data"][row["month"].strftime('%b')] = round(row["settlement_ratio"], 2)

    avg_tat_per_month = Claim.objects.filter(date_dv_issued__year=2026).annotate(
        month=TruncMonth('date_dv_issued')
    ).values('month').annotate(avg_tat=Avg('tat_dv')).order_by('month')

    final_avg_tat_per_month = []

    for row in avg_tat_per_month:
        row['month'] = row['month'].strftime('%b')
        row['avg_tat'] = round(row['avg_tat'], 2)
        final_avg_tat_per_month.append(row)

    average_settlement_ratio = Claim.objects.filter(closure_date__year=2026, status='Closed').annotate(
        month=TruncMonth('closure_date')
    ).values('month').annotate(
        total_closed=Count('id'),
        paid_claims=Count('id', filter=Q(sub_status='Paid'))
    ).annotate(settlement_ratio=Cast('paid_claims', FloatField()) / F('total_closed') * 100).order_by('month')

    final_avg_settlement_ratio = []

    for row in average_settlement_ratio:
        row['month'] = row['month'].strftime('%b')
        row['settlement_ratio'] = round(row['settlement_ratio'], 2)
        final_avg_settlement_ratio.append(row)



    context = {
        "lodged_closed_trends": final_combined_lodged_closed_trend,
        "settlement_ratio_per_underwriter_per_month": each_underwriter_data,
        "avg_tat_data_per_month": final_avg_tat_per_month,
        "avg_settlement_ratio_per_month": final_avg_settlement_ratio,
    }


    return render(request, 'reports_trends_page.html', context)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_csv_to_excel(request):
    claims = Claim.objects.all()

    # Step 1: Create CSV in memory
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)

    # Header row
    writer.writerow([
        "Id",
        "Category",
        "Intimation Date",
        "Name of Insured",
        "Date of Loss",
        "Documented",
        "Date Fully Documented",
        "Underwriter",
        "Branch",
        "Handler",
        "Status",
        "Sub Status",
        "Notes",
        "Closure Date",
        "TAT_CL",
        "TAT_DV",
        "Circumstance",
        "Sum Insured",
        "Date DV Issued",
        "DV Amount",
        "Date DV Returned",
        "Amount Paid",
        "Created At",
        "Updated At",
    ])

    # Write rows from queryset
    for row in claims:
        writer.writerow([
            row.id,
            row.category,
            row.intimation_date,
            row.name_of_insured,
            row.date_of_loss,
            row.documented,
            row.date_fully_documented,
            row.underwriter,
            row.branch,
            row.handler,
            row.status,
            row.sub_status,
            row.notes,
            row.closure_date,
            row.tat_cl,
            row.tat_dv,
            row.circumstance,
            row.sum_insured,
            row.date_dv_issued,
            row.dv_amount,
            row.date_dv_returned,
            row.amount_paid,
            row.created_at,
            row.updated_at,
        ])

    csv_buffer.seek(0)  # rewind to start

    # Step 2: Convert CSV to Excel using XlsxWriter
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Sheet1")

    reader = csv.reader(csv_buffer)
    for row_idx, row in enumerate(reader):
        for col_idx, value in enumerate(row):
            worksheet.write(row_idx, col_idx, value)

    workbook.close()
    output.seek(0)

    # Step 3: Send Excel file to client
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = 'attachment; filename="download_test.xlsx"'

    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def io_testing(request):
    # buffer = io.StringIO()  # in‑memory text file
    # writer = csv.writer(buffer)
    #
    # # Header
    # writer.writerow(["Id", "Name", "Status"])
    #
    # # Sample rows
    # writer.writerow([1, "John Doe", "Pending"])
    # writer.writerow([2, "Jane Smith", "Closed"])
    #
    # buffer.seek(0)  # rewind
    #
    # return HttpResponse(
    #     buffer.getvalue(),
    #     content_type="text/csv"
    # )
    output = io.BytesIO()  # in‑memory binary file
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet()

    # Header
    worksheet.write(0, 0, "Id")
    worksheet.write(0, 1, "Name")
    worksheet.write(0, 2, "Status")

    # Sample rows
    worksheet.write(1, 0, 1)
    worksheet.write(1, 1, "John Doe")
    worksheet.write(1, 2, "Pending")

    worksheet.write(2, 0, 2)
    worksheet.write(2, 1, "Jane Smith")
    worksheet.write(2, 2, "Closed")

    workbook.close()
    output.seek(0)

    return HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )





#==================APIs==========================
#================================================

@login_required(login_url='login_page')
@require_POST
def download_pending_claims(request):
    # Accept JSON bodies (fetch/ajax with application/json) or form-encoded posts
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            data = {}
    else:
        data = request.POST

    branch_filter = data.get('branchFilter')
    handler_filter = data.get('handlerFilter')
    underwriter_filter = data.get('underwriterFilter')
    category_filter = data.get('categoryFilter')
    sub_status = data.get('subStatusFilter')

    if category_filter == "Motor":
        base_qs = Claim.objects.filter(status='Pending', category="Motor").select_related('motor_details').defer(
            'created_at', 'updated_at', 'status', 'date_dv_issued', 'dv_amount',
            'date_dv_returned', 'amount_paid', 'tat_cl', 'tat_dv', 'closure_date'
        )
    elif category_filter == "Non_Motor":
        base_qs = Claim.objects.filter(status='Pending', category="Non_Motor").select_related('non_motor_details').defer(
            'created_at', 'updated_at', 'status', 'date_dv_issued', 'dv_amount',
            'date_dv_returned', 'amount_paid', 'tat_cl', 'tat_dv', 'closure_date'
        )
    elif category_filter == "Credit_Life":
        base_qs = Claim.objects.filter(status='Pending', category="Credit_Life").select_related(
            'credit_life_details').defer(
            'created_at', 'updated_at', 'status', 'date_dv_issued', 'dv_amount',
            'date_dv_returned', 'amount_paid', 'tat_cl', 'tat_dv', 'closure_date'
        )
    elif category_filter == "":
        base_qs = Claim.objects.filter(status='Pending').select_related(
            'motor_details', 'non_motor_details', 'credit_life_details'
        ).defer('created_at', 'updated_at', 'status', 'date_dv_issued', 'dv_amount',
            'date_dv_returned', 'amount_paid', 'tat_cl', 'tat_dv', 'closure_date')
    else:
        return JsonResponse({'error': 'Invalid category filter'}, status=400)

    filtered_qs = base_qs

    if sub_status:
        filtered_qs = base_qs.filter(sub_status=sub_status)
    if handler_filter:
        filtered_qs = filtered_qs.filter(handler=handler_filter)
    if underwriter_filter:
        filtered_qs = filtered_qs.filter(underwriter=underwriter_filter)
    if branch_filter:
        filtered_qs = filtered_qs.filter(branch=branch_filter)

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    if category_filter == "Motor":
        writer.writerow([
            'Claim Id',
            'Client',
            'category',
            'Registration Number',
            'Motor Class',
            'circumstance',
            'Sum Insured',
            'Status',
            'Sub Status',
            'Intimation Date',
            'Date of Loss',
            'Documented?',
            'Date Fully Documented',
            'Underwriter',
            'Handler',
            'Branch',
            'Notes',
            'Assessor'
        ])

        for claim in filtered_qs:
            writer.writerow([
                claim.id,
                claim.name_of_insured,
                claim.category,
                claim.motor_details.registration_number,
                claim.motor_details.motor_class,
                claim.circumstance,
                claim.sum_insured,
                "Pending",
                claim.sub_status,
                claim.intimation_date.strftime("%d-%m-%Y") if claim.intimation_date else "",
                claim.date_of_loss.strftime("%d-%m-%Y") if claim.date_of_loss else "",
                "Yes" if claim.documented else "No",
                claim.date_fully_documented.strftime("%d-%m-%Y") if claim.date_fully_documented else "",
                claim.underwriter,
                claim.handler,
                claim.branch,
                claim.notes or "",
                claim.motor_details.assessor or ""

            ])

    elif category_filter == "Non_Motor":
        writer.writerow([
            'Claim Id',
            'Client',
            'category',
            'Cover Type',
            'circumstance',
            'Sum Insured',
            'Status',
            'Sub Status',
            'Intimation Date',
            'Date of Loss',
            'Documented?',
            'Date Fully Documented',
            'Underwriter',
            'Handler',
            'Branch',
            'Notes',


        ])

        for claim in filtered_qs:
            writer.writerow([
                claim.id,
                claim.name_of_insured,
                "Non-Motor" if claim.category else "",
                claim.non_motor_details.cover_type,
                claim.circumstance,
                claim.sum_insured,
                "Pending",
                claim.sub_status,
                claim.intimation_date.strftime("%d-%m-%Y") if claim.intimation_date else "",
                claim.date_of_loss.strftime("%d-%m-%Y") if claim.date_of_loss else "",
                "Yes" if claim.documented else "No",
                claim.date_fully_documented.strftime("%d-%m-%Y") if claim.date_fully_documented else "",
                claim.underwriter,
                claim.handler,
                claim.branch,
                claim.notes or "",

            ])

    elif category_filter == "Credit_Life":
        writer.writerow([
            'Claim Id',
            'Client',
            'category',
            'Claim Trigger',
            'circumstance',
            'Sum Insured',
            'Status',
            'Sub Status',
            'Intimation Date',
            'Date of Loss',
            'Documented?',
            'Date Fully Documented',
            'Underwriter',
            'Handler',
            'Branch',
            'Notes',


        ])

        for claim in filtered_qs:
            writer.writerow([
                claim.id,
                claim.name_of_insured,
                "Credit Life" if claim.category else "",
                claim.credit_life_details.claim_trigger,
                claim.circumstance,
                claim.sum_insured,
                "Pending",
                claim.sub_status,
                claim.intimation_date.strftime("%d-%m-%Y") if claim.intimation_date else "",
                claim.date_of_loss.strftime("%d-%m-%Y") if claim.date_of_loss else "",
                "Yes" if claim.documented else "No",
                claim.date_fully_documented.strftime("%d-%m-%Y") if claim.date_fully_documented else "",
                claim.underwriter,
                claim.handler,
                claim.branch,
                claim.notes or "",

            ])

    elif category_filter == "":
        category_map = {
            "Motor": "Motor",
            "Non_Motor": "Non-Motor",
            "Credit_Life": "Credit Life",
        }

        writer.writerow([
            'Claim Id',
            'Client',
            'category',
            'circumstance',
            'Sum Insured',
            'Status',
            'Sub Status',
            'Intimation Date',
            'Date of Loss',
            'Documented?',
            'Date Fully Documented',
            'Underwriter',
            'Handler',
            'Branch',
            'Notes',
            'Registration Number',
            'Motor Class',
            'Assessor',
            'Cover Type',
            'Claim Trigger'
        ])

        for claim in filtered_qs:
            motor = getattr(claim, 'motor_details', None)
            non_motor = getattr(claim, 'non_motor_details', None)
            credit = getattr(claim, 'credit_life_details', None)
            category_display = category_map.get(claim.category, "")

            writer.writerow([
                claim.id,
                claim.name_of_insured,
                category_display,
                claim.circumstance,
                claim.sum_insured,
                "Pending",
                claim.sub_status,
                claim.intimation_date.strftime("%d-%m-%Y") if claim.intimation_date else "",
                claim.date_of_loss.strftime("%d-%m-%Y") if claim.date_of_loss else "",
                "Yes" if claim.documented else "No",
                claim.date_fully_documented.strftime("%d-%m-%Y") if claim.date_fully_documented else "",
                claim.underwriter,
                claim.handler,
                claim.branch,
                claim.notes or "",
                (motor.registration_number if motor else "") or "",
                (motor.motor_class if motor else "") or "",
                (motor.assessor if motor else "") or "",
                (non_motor.cover_type if non_motor else "") or "",
                (credit.claim_trigger if credit else "") or "",
            ])

    else:
        return JsonResponse({"error": "Invalid Category!"}, status=400)

    buffer.seek(0)
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet(f"Pending_claims_report_{datetime.now().strftime('%H%M%S')}")
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#0F1F38', 'font_color': 'white'})
    id_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'font_color': 'black'})

    reader = csv.reader(buffer)

    for row_id, row in enumerate(reader):
        for col, value in enumerate(row):
            if row_id == 0:
                worksheet.write(row_id, col, value, header_fmt)
            else:
                if col == 0:
                    worksheet.write(row_id, col, value, id_fmt)
                else:
                    worksheet.write(row_id, col, value)

    workbook.close()
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response[
        'Content-Disposition'] = f'attachment; filename=Pending_Claims_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.xlsx'

    return response

@login_required(login_url='login_page')
@require_POST
def download_closed_claims(request):
    # Accept JSON bodies (fetch/ajax with application/json) or form-encoded posts
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            data = {}
    else:
        data = request.POST

    branch_filter = data.get('branchFilter')
    handler_filter = data.get('handlerFilter')
    underwriter_filter = data.get('underwriterFilter')
    category_filter = data.get('categoryFilter')
    sub_status = data.get('subStatusFilter')

    if category_filter == "Motor":
        base_qs = Claim.objects.filter(status='Closed', category="Motor").select_related('motor_details').defer(
            'created_at', 'updated_at', 'status'
        )
    elif category_filter == "Non_Motor":
        base_qs = Claim.objects.filter(status='Closed', category="Non_Motor").select_related('non_motor_details').defer(
            'created_at', 'updated_at', 'status'
        )
    elif category_filter == "Credit_Life":
        base_qs = Claim.objects.filter(status='Closed', category="Credit_Life").select_related('credit_life_details').defer(
            'created_at', 'updated_at', 'status'
        )
    elif category_filter == "":
        base_qs = Claim.objects.filter(status='Closed').select_related(
            'motor_details', 'non_motor_details', 'credit_life_details'
        ).defer('created_at', 'updated_at', 'status')
    else:
        return JsonResponse({'error': 'Invalid category filter'}, status=400)

    filtered_qs = base_qs

    if sub_status:
        filtered_qs = base_qs.filter(sub_status=sub_status)
    if handler_filter:
        filtered_qs = filtered_qs.filter(handler=handler_filter)
    if underwriter_filter:
        filtered_qs = filtered_qs.filter(underwriter=underwriter_filter)
    if branch_filter:
        filtered_qs = filtered_qs.filter(branch=branch_filter)

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    if category_filter == "Motor":
        writer.writerow([
            'Claim Id',
            'Client',
            'category',
            'Registration Number',
            'Motor Class',
            'circumstance',
            'Sum Insured',
            'Status',
            'Sub Status',
            'Intimation Date',
            'Date of Loss',
            'Documented?',
            'Date Fully Documented',
            'Underwriter',
            'Handler',
            'Branch',
            'Notes',
            'Date DV Issued',
            'DV Amount',
            'Date DV Returned',
            'Closure Date',
            'Tat DV',
            'Tat Cl',
            'Amount Paid',
            'Assessor'
        ])

        for claim in filtered_qs:
            writer.writerow([
                claim.id,
                claim.name_of_insured,
                claim.category,
                claim.motor_details.registration_number,
                claim.motor_details.motor_class,
                claim.circumstance,
                claim.sum_insured,
                "Closed",
                claim.sub_status,
                claim.intimation_date.strftime("%d-%m-%Y") if claim.intimation_date else "",
                claim.date_of_loss.strftime("%d-%m-%Y") if claim.date_of_loss else "",
                "Yes" if claim.documented else "No",
                claim.date_fully_documented.strftime("%d-%m-%Y") if claim.date_fully_documented else "",
                claim.underwriter,
                claim.handler,
                claim.branch,
                claim.notes or "",
                claim.date_dv_issued.strftime("%d-%m-%Y") if claim.date_dv_issued else "",
                claim.dv_amount or "",
                claim.date_dv_returned.strftime("%d-%m-%Y") if claim.date_dv_returned else "",
                claim.closure_date.strftime("%d-%m-%Y") if claim.closure_date else "",
                claim.tat_dv or "",
                claim.tat_cl or "",
                claim.amount_paid or "",
                claim.motor_details.assessor or ""

            ])

    elif category_filter == "Non_Motor":
        writer.writerow([
            'Claim Id',
            'Client',
            'category',
            'Cover Type',
            'circumstance',
            'Sum Insured',
            'Status',
            'Sub Status',
            'Intimation Date',
            'Date of Loss',
            'Documented?',
            'Date Fully Documented',
            'Underwriter',
            'Handler',
            'Branch',
            'Notes',
            'Date DV Issued',
            'DV Amount',
            'Date DV Returned',
            'Closure Date',
            'Tat DV',
            'Tat Cl',
            'Amount Paid',

        ])

        for claim in filtered_qs:
            writer.writerow([
                claim.id,
                claim.name_of_insured,
                "Non-Motor" if claim.category else "",
                claim.non_motor_details.cover_type,
                claim.circumstance,
                claim.sum_insured,
                "Closed",
                claim.sub_status,
                claim.intimation_date.strftime("%d-%m-%Y") if claim.intimation_date else "",
                claim.date_of_loss.strftime("%d-%m-%Y") if claim.date_of_loss else "",
                "Yes" if claim.documented else "No",
                claim.date_fully_documented.strftime("%d-%m-%Y") if claim.date_fully_documented else "",
                claim.underwriter,
                claim.handler,
                claim.branch,
                claim.notes or "",
                claim.date_dv_issued.strftime("%d-%m-%Y") if claim.date_dv_issued else "",
                claim.dv_amount or "",
                claim.date_dv_returned.strftime("%d-%m-%Y") if claim.date_dv_returned else "",
                claim.closure_date.strftime("%d-%m-%Y") if claim.closure_date else "",
                claim.tat_dv or "",
                claim.tat_cl or "",
                claim.amount_paid or "",

            ])

    elif category_filter == "Credit_Life":
        writer.writerow([
            'Claim Id',
            'Client',
            'category',
            'Claim Trigger',
            'circumstance',
            'Sum Insured',
            'Status',
            'Sub Status',
            'Intimation Date',
            'Date of Loss',
            'Documented?',
            'Date Fully Documented',
            'Underwriter',
            'Handler',
            'Branch',
            'Notes',
            'Date DV Issued',
            'DV Amount',
            'Date DV Returned',
            'Closure Date',
            'Tat DV',
            'Tat Cl',
            'Amount Paid',

        ])

        for claim in filtered_qs:
            writer.writerow([
                claim.id,
                claim.name_of_insured,
                "Credit Life" if claim.category else "",
                claim.credit_life_details.claim_trigger,
                claim.circumstance,
                claim.sum_insured,
                "Closed",
                claim.sub_status,
                claim.intimation_date.strftime("%d-%m-%Y") if claim.intimation_date else "",
                claim.date_of_loss.strftime("%d-%m-%Y") if claim.date_of_loss else "",
                "Yes" if claim.documented else "No",
                claim.date_fully_documented.strftime("%d-%m-%Y") if claim.date_fully_documented else "",
                claim.underwriter,
                claim.handler,
                claim.branch,
                claim.notes or "",
                claim.date_dv_issued.strftime("%d-%m-%Y") if claim.date_dv_issued else "",
                claim.dv_amount or "",
                claim.date_dv_returned.strftime("%d-%m-%Y") if claim.date_dv_returned else "",
                claim.closure_date.strftime("%d-%m-%Y") if claim.closure_date else "",
                claim.tat_dv or "",
                claim.tat_cl or "",
                claim.amount_paid or "",

            ])

    elif category_filter == "":
        category_map = {
            "Motor": "Motor",
            "Non_Motor": "Non-Motor",
            "Credit_Life": "Credit Life",
        }

        writer.writerow([
            'Claim Id',
            'Client',
            'category',
            'circumstance',
            'Sum Insured',
            'Status',
            'Sub Status',
            'Intimation Date',
            'Date of Loss',
            'Documented?',
            'Date Fully Documented',
            'Underwriter',
            'Handler',
            'Branch',
            'Notes',
            'Date DV Issued',
            'DV Amount',
            'Date DV Returned',
            'Closure Date',
            'Tat DV',
            'Tat Cl',
            'Amount Paid',
            'Registration Number',
            'Motor Class',
            'Assessor',
            'Cover Type',
            'Claim Trigger'
        ])

        for claim in filtered_qs:
            motor = getattr(claim, 'motor_details', None)
            non_motor = getattr(claim, 'non_motor_details', None)
            credit = getattr(claim, 'credit_life_details', None)
            category_display = category_map.get(claim.category, "")

            writer.writerow([
                claim.id,
                claim.name_of_insured,
                category_display,
                claim.circumstance,
                claim.sum_insured,
                "Closed",
                claim.sub_status,
                claim.intimation_date.strftime("%d-%m-%Y") if claim.intimation_date else "",
                claim.date_of_loss.strftime("%d-%m-%Y") if claim.date_of_loss else "",
                "Yes" if claim.documented else "No",
                claim.date_fully_documented.strftime("%d-%m-%Y") if claim.date_fully_documented else "",
                claim.underwriter,
                claim.handler,
                claim.branch,
                claim.notes or "",
                claim.date_dv_issued.strftime("%d-%m-%Y") if claim.date_dv_issued else "",
                claim.dv_amount or "",
                claim.date_dv_returned.strftime("%d-%m-%Y") if claim.date_dv_returned else "",
                claim.closure_date.strftime("%d-%m-%Y") if claim.closure_date else "",
                claim.tat_dv or "",
                claim.tat_cl or "",
                claim.amount_paid or "",
                (motor.registration_number if motor else "") or "",
                (motor.motor_class if motor else "") or "",
                (motor.assessor if motor else "") or "",
                (non_motor.cover_type if non_motor else "") or "",
                (credit.claim_trigger if credit else "") or "",
            ])

    else:
        return JsonResponse({"error": "Invalid Category!"}, status=400)

    buffer.seek(0)
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet(f"Closed_claims_report_{datetime.now().strftime('%H%M%S')}")
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#0F1F38', 'font_color': 'white'})
    id_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'font_color': 'black'})

    reader = csv.reader(buffer)

    for row_id, row in enumerate(reader):
        for col, value in enumerate(row):
            if row_id == 0:
                worksheet.write(row_id, col, value, header_fmt)
            else:
                if col == 0:
                    worksheet.write(row_id, col, value, id_fmt)
                else:
                    worksheet.write(row_id, col, value)

    workbook.close()
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response['Content-Disposition'] = f'attachment; filename=Closed_Claims_Report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.xlsx'

    return response

@login_required(login_url='login_page')
@require_POST
def download_total_claims(request):
    # Accept JSON bodies (fetch/ajax with application/json) or form-encoded posts
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            data = {}
    else:
        data = request.POST

    status_filter = data.get('statusFilter')
    handler_filter = data.get('handlerFilter')
    underwriter_filter = data.get('underwriterFilter')
    category_filter = data.get('categoryFilter')
    branch_filter = data.get('branchFilter')

    if category_filter == "Motor":
        base_qs = Claim.objects.filter(category="Motor").select_related('motor_details').defer(
            'created_at', 'updated_at'
        )
    elif category_filter == "Non_Motor":
        base_qs = Claim.objects.filter(category="Non_Motor").select_related('non_motor_details').defer(
            'created_at', 'updated_at'
        )
    elif category_filter == "Credit_Life":
        base_qs = Claim.objects.filter(category="Credit_Life").select_related('credit_life_details').defer(
            'created_at', 'updated_at'
        )
    elif category_filter == "":
        base_qs = Claim.objects.select_related(
            'motor_details', 'non_motor_details', 'credit_life_details'
        ).defer('created_at', 'updated_at')
    else:
        return JsonResponse({'error': 'Invalid category filter'}, status=400)

    filtered_qs = base_qs

    if status_filter:
        filtered_qs = base_qs.filter(status=status_filter)
    if handler_filter:
        filtered_qs = filtered_qs.filter(handler=handler_filter)
    if underwriter_filter:
        filtered_qs = filtered_qs.filter(underwriter=underwriter_filter)
    if branch_filter:
        filtered_qs = filtered_qs.filter(branch=branch_filter)

    buffer = io.StringIO()
    writer = csv.writer(buffer)

    if category_filter == "Motor":
        writer.writerow([
            'Claim Id',
            'Client',
            'category',
            'Registration Number',
            'Motor Class',
            'circumstance',
            'Sum Insured',
            'Status',
            'Sub Status',
            'Intimation Date',
            'Date of Loss',
            'Documented?',
            'Date Fully Documented',
            'Underwriter',
            'Handler',
            'Branch',
            'Notes',
            'Date DV Issued',
            'DV Amount',
            'Date DV Returned',
            'Closure Date',
            'Tat DV',
            'Tat Cl',
            'Amount Paid',
            'Assessor'
        ])

        for claim in filtered_qs:
            writer.writerow([
                claim.id,
                claim.name_of_insured,
                claim.category,
                claim.motor_details.registration_number,
                claim.motor_details.motor_class,
                claim.circumstance,
                claim.sum_insured,
                claim.status,
                claim.sub_status,
                claim.intimation_date.strftime("%d-%m-%Y") if claim.intimation_date else "",
                claim.date_of_loss.strftime("%d-%m-%Y") if claim.date_of_loss else "",
                "Yes" if claim.documented else "No",
                claim.date_fully_documented.strftime("%d-%m-%Y") if claim.date_fully_documented else "",
                claim.underwriter,
                claim.handler,
                claim.branch,
                claim.notes or "",
                claim.date_dv_issued.strftime("%d-%m-%Y") if claim.date_dv_issued else "",
                claim.dv_amount or "",
                claim.date_dv_returned.strftime("%d-%m-%Y") if claim.date_dv_returned else "",
                claim.closure_date.strftime("%d-%m-%Y") if claim.closure_date else "",
                claim.tat_dv or "",
                claim.tat_cl or "",
                claim.amount_paid or "",
                claim.motor_details.assessor or ""

            ])

    elif category_filter == "Non_Motor":
        writer.writerow([
            'Claim Id',
            'Client',
            'category',
            'Cover Type',
            'circumstance',
            'Sum Insured',
            'Status',
            'Sub Status',
            'Intimation Date',
            'Date of Loss',
            'Documented?',
            'Date Fully Documented',
            'Underwriter',
            'Handler',
            'Branch',
            'Notes',
            'Date DV Issued',
            'DV Amount',
            'Date DV Returned',
            'Closure Date',
            'Tat DV',
            'Tat Cl',
            'Amount Paid',

        ])

        for claim in filtered_qs:
            writer.writerow([
                claim.id,
                claim.name_of_insured,
                "Non-Motor" if claim.category else "",
                claim.non_motor_details.cover_type,
                claim.circumstance,
                claim.sum_insured,
                claim.status,
                claim.sub_status,
                claim.intimation_date.strftime("%d-%m-%Y") if claim.intimation_date else "",
                claim.date_of_loss.strftime("%d-%m-%Y") if claim.date_of_loss else "",
                "Yes" if claim.documented else "No",
                claim.date_fully_documented.strftime("%d-%m-%Y") if claim.date_fully_documented else "",
                claim.underwriter,
                claim.handler,
                claim.branch,
                claim.notes or "",
                claim.date_dv_issued.strftime("%d-%m-%Y") if claim.date_dv_issued else "",
                claim.dv_amount or "",
                claim.date_dv_returned.strftime("%d-%m-%Y") if claim.date_dv_returned else "",
                claim.closure_date.strftime("%d-%m-%Y") if claim.closure_date else "",
                claim.tat_dv or "",
                claim.tat_cl or "",
                claim.amount_paid or "",

            ])

    elif category_filter == "Credit_Life":
        writer.writerow([
            'Claim Id',
            'Client',
            'category',
            'Claim Trigger',
            'circumstance',
            'Sum Insured',
            'Status',
            'Sub Status',
            'Intimation Date',
            'Date of Loss',
            'Documented?',
            'Date Fully Documented',
            'Underwriter',
            'Handler',
            'Branch',
            'Notes',
            'Date DV Issued',
            'DV Amount',
            'Date DV Returned',
            'Closure Date',
            'Tat DV',
            'Tat Cl',
            'Amount Paid',

        ])

        for claim in filtered_qs:
            writer.writerow([
                claim.id,
                claim.name_of_insured,
                "Credit Life" if claim.category else "",
                claim.credit_life_details.claim_trigger,
                claim.circumstance,
                claim.sum_insured,
                claim.status,
                claim.sub_status,
                claim.intimation_date.strftime("%d-%m-%Y") if claim.intimation_date else "",
                claim.date_of_loss.strftime("%d-%m-%Y") if claim.date_of_loss else "",
                "Yes" if claim.documented else "No",
                claim.date_fully_documented.strftime("%d-%m-%Y") if claim.date_fully_documented else "",
                claim.underwriter,
                claim.handler,
                claim.branch,
                claim.notes or "",
                claim.date_dv_issued.strftime("%d-%m-%Y") if claim.date_dv_issued else "",
                claim.dv_amount or "",
                claim.date_dv_returned.strftime("%d-%m-%Y") if claim.date_dv_returned else "",
                claim.closure_date.strftime("%d-%m-%Y") if claim.closure_date else "",
                claim.tat_dv or "",
                claim.tat_cl or "",
                claim.amount_paid or "",

                ])

    elif category_filter == "":
        category_map = {
            "Motor": "Motor",
            "Non_Motor": "Non-Motor",
            "Credit_Life": "Credit Life",
        }

        writer.writerow([
            'Claim Id',
            'Client',
            'category',
            'circumstance',
            'Sum Insured',
            'Status',
            'Sub Status',
            'Intimation Date',
            'Date of Loss',
            'Documented?',
            'Date Fully Documented',
            'Underwriter',
            'Handler',
            'Branch',
            'Notes',
            'Date DV Issued',
            'DV Amount',
            'Date DV Returned',
            'Closure Date',
            'Tat DV',
            'Tat Cl',
            'Amount Paid',
            'Registration Number',
            'Motor Class',
            'Assessor',
            'Cover Type',
            'Claim Trigger'
        ])

        for claim in filtered_qs:
            motor = getattr(claim, 'motor_details', None)
            non_motor = getattr(claim, 'non_motor_details', None)
            credit = getattr(claim, 'credit_life_details', None)
            category_display = category_map.get(claim.category, "")

            writer.writerow([
                claim.id,
                claim.name_of_insured,
                category_display,
                claim.circumstance,
                claim.sum_insured,
                claim.status,
                claim.sub_status,
                claim.intimation_date.strftime("%d-%m-%Y") if claim.intimation_date else "",
                claim.date_of_loss.strftime("%d-%m-%Y") if claim.date_of_loss else "",
                "Yes" if claim.documented else "No",
                claim.date_fully_documented.strftime("%d-%m-%Y") if claim.date_fully_documented else "",
                claim.underwriter,
                claim.handler,
                claim.branch,
                claim.notes or "",
                claim.date_dv_issued.strftime("%d-%m-%Y") if claim.date_dv_issued else "",
                claim.dv_amount or "",
                claim.date_dv_returned.strftime("%d-%m-%Y") if claim.date_dv_returned else "",
                claim.closure_date.strftime("%d-%m-%Y") if claim.closure_date else "",
                claim.tat_dv or "",
                claim.tat_cl or "",
                claim.amount_paid or "",
                (motor.registration_number if motor else "") or "",
                (motor.motor_class if motor else "") or "",
                (motor.assessor if motor else "") or "",
                (non_motor.cover_type if non_motor else "") or "",
                (credit.claim_trigger if credit else "") or "",
            ])

    else:
        return JsonResponse({"error": "Invalid Category!"}, status=400)

    buffer.seek(0)
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet(f"Claims_report_{datetime.now().strftime('%d%m%Y_%H%M%S')}")
    header_fmt = workbook.add_format({'bold': True, 'bg_color': '#0F1F38', 'font_color': 'white'})
    id_fmt = workbook.add_format({'bold': True, 'bg_color': '#FFFF00', 'font_color': 'black'})


    reader =csv.reader(buffer)

    for row_id, row in enumerate(reader):
        for col, value in enumerate(row):
            if row_id == 0:
                worksheet.write(row_id, col, value, header_fmt)
            else:
                if col == 0:
                    worksheet.write(row_id, col, value, id_fmt)
                else:
                    worksheet.write(row_id, col, value)

    workbook.close()
    output.seek(0)

    response = HttpResponse(
            output.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    response['Content-Disposition'] = f'attachment; filename=Claims_report_{datetime.now().strftime('%d%m%Y_%H%M%S')}.xlsx'

    return response

@login_required(login_url='login_page')
@require_GET
def pending_claims_details_one(request, claim_id, claim_category):
    if claim_category == "Motor":
        claim_instance = Claim.objects.with_days_pending().filter(status="Pending").select_related('motor_details').values(
            'documented', 'date_fully_documented', 'sub_status', 'notes', 'closure_date', 'tat_cl',
            'tat_dv', 'circumstance', 'date_dv_issued', 'dv_amount', 'date_dv_returned', 'dv_amount',
            'date_dv_returned', 'amount_paid', 'created_at', 'updated_at', 'motor_details__registration_number',
            'motor_details__motor_class', 'motor_details__assessor', 'days_pending'
        ).get(id=claim_id)
        data = {
            "documented": "Yes" if claim_instance['documented'] else "No",
            "date_fully_documented": claim_instance['date_fully_documented'].strftime('%Y-%m-%d') if claim_instance[
                "date_fully_documented"] else "",
            "sub_status": claim_instance['sub_status'],
            "notes": claim_instance['notes'] or "",
            "closure_date": claim_instance['closure_date'].strftime('%Y-%m-%d') if claim_instance[
                'closure_date'] else "",
            "tat_cl": claim_instance['tat_cl'] or "",
            "tat_dv": claim_instance['tat_dv'] or "",
            "circumstance": claim_instance['circumstance'],
            "date_dv_issued": claim_instance['date_dv_issued'].strftime('%Y-%m-%d') if claim_instance[
                'date_dv_issued'] else "",
            "dv_amount": claim_instance['dv_amount'] or "",
            "date_dv_returned": claim_instance['date_dv_returned'].strftime('%Y-%m-%d') if claim_instance[
                'date_dv_returned'] else "",
            "amount_paid": claim_instance['amount_paid'] or "",
            "created_at": claim_instance['created_at'].strftime('%Y-%m-%d') if claim_instance['created_at'] else "",
            "updated_at": claim_instance['updated_at'].strftime('%Y-%m-%d') if claim_instance['created_at'] else "",
            "registration_number": claim_instance['motor_details__registration_number'],
            "motor_class": claim_instance['motor_details__motor_class'],
            "assessor": claim_instance['motor_details__assessor'] or "",
            "days_pending": claim_instance['days_pending'] or "__Closed__",
            "status": "Pending"
        }

    elif claim_category == "Non_Motor":
        claim_instance = Claim.objects.with_days_pending().filter(status="Pending").select_related('non_motor_details').values(
            'documented', 'date_fully_documented', 'sub_status', 'notes', 'closure_date', 'tat_cl',
            'tat_dv', 'circumstance', 'date_dv_issued', 'dv_amount', 'date_dv_returned', 'dv_amount',
            'date_dv_returned', 'amount_paid', 'created_at', 'updated_at', 'non_motor_details__cover_type',
            'days_pending'
        ).get(id=claim_id)
        data = {
            "documented": "Yes" if claim_instance['documented'] else "No",
            "date_fully_documented": claim_instance['date_fully_documented'].strftime('%Y-%m-%d') if claim_instance[
                'date_fully_documented'] else "",
            "sub_status": claim_instance['sub_status'],
            "notes": claim_instance['notes'] or "",
            "closure_date": claim_instance['closure_date'].strftime('%Y-%m-%d') if claim_instance[
                'closure_date'] else "",
            "tat_cl": claim_instance['tat_cl'] or "",
            "tat_dv": claim_instance['tat_dv'] or "",
            "circumstance": claim_instance['circumstance'],
            "date_dv_issued": claim_instance['date_dv_issued'].strftime('%Y-%m-%d') if claim_instance[
                'date_dv_issued'] else "",
            "dv_amount": claim_instance['dv_amount'] or "",
            "date_dv_returned": claim_instance['date_dv_returned'].strftime('%Y-%m-%d') if claim_instance[
                'date_dv_returned'] else "",
            "amount_paid": claim_instance['amount_paid'] or "",
            "created_at": claim_instance['created_at'].strftime('%Y-%m-%d') if claim_instance['created_at'] else "",
            "updated_at": claim_instance['updated_at'].strftime('%Y-%m-%d') if claim_instance['updated_at'] else "",
            "days_pending": claim_instance['days_pending'] or "__Closed__",
            "cover_type": claim_instance['non_motor_details__cover_type'] or "",
            "status": "Pending"
        }

    elif claim_category == "Credit_Life":
        claim_instance = Claim.objects.with_days_pending().filter(status="Pending").select_related('credit_life_details').values(
            'documented', 'date_fully_documented', 'sub_status', 'notes', 'closure_date', 'tat_cl',
            'tat_dv', 'circumstance', 'date_dv_issued', 'dv_amount', 'date_dv_returned', 'dv_amount',
            'date_dv_returned', 'amount_paid', 'created_at', 'updated_at', 'credit_life_details__claim_trigger',
            'days_pending'
        ).get(id=claim_id)
        data = {
            "documented": "Yes" if claim_instance['documented'] else "No",
            "date_fully_documented": claim_instance['date_fully_documented'].strftime('%Y-%m-%d') if claim_instance[
                'date_fully_documented'] else "",

            "sub_status": claim_instance['sub_status'],
            "notes": claim_instance['notes'] or "",
            "closure_date": claim_instance['closure_date'].strftime('%Y-%m-%d') if claim_instance[
                'closure_date'] else "",
            "tat_cl": claim_instance['tat_cl'] or "",
            "tat_dv": claim_instance['tat_dv'] or "",
            "circumstance": claim_instance['circumstance'],
            "date_dv_issued": claim_instance['date_dv_issued'].strftime('%Y-%m-%d') if claim_instance[
                'date_dv_issued'] else "",
            "dv_amount": claim_instance['dv_amount'] or "",
            "date_dv_returned": claim_instance['date_dv_returned'].strftime('%Y-%m-%d') if claim_instance[
                'date_dv_returned'] else "",
            "amount_paid": claim_instance['amount_paid'] or "",
            "created_at": claim_instance['created_at'].strftime('%Y-%m-%d') if claim_instance['created_at'] else "",
            "updated_at": claim_instance['updated_at'].strftime('%Y-%m-%d') if claim_instance['updated_at'] else "",
            "claim_trigger": claim_instance['credit_life_details__claim_trigger'],
            "days_pending": claim_instance['days_pending'] or "__Closed__",
            "status": "Pending"
        }

    else:
        return JsonResponse({"error": "Invalid Category!"}, status=400)

    return JsonResponse(data, safe=False)

@login_required(login_url='login_page')
@require_GET
def closed_claims_details_one(request, claim_id, claim_category):
    if claim_category == "Motor":
        claim_instance = Claim.objects.with_days_pending().filter(status="Closed").select_related('motor_details').values(
            'documented', 'date_fully_documented', 'sub_status', 'notes', 'closure_date', 'tat_cl',
            'tat_dv', 'circumstance', 'date_dv_issued', 'dv_amount', 'date_dv_returned', 'dv_amount',
            'date_dv_returned', 'amount_paid', 'created_at', 'updated_at', 'motor_details__registration_number',
            'motor_details__motor_class', 'motor_details__assessor', 'days_pending'
        ).get(id=claim_id)
        data = {
            "documented": "Yes" if claim_instance['documented'] else "No",
            "date_fully_documented": claim_instance['date_fully_documented'].strftime('%Y-%m-%d') if claim_instance[
                "date_fully_documented"] else "",
            "sub_status": claim_instance['sub_status'],
            "notes": claim_instance['notes'] or "",
            "closure_date": claim_instance['closure_date'].strftime('%Y-%m-%d') if claim_instance[
                'closure_date'] else "",
            "tat_cl": claim_instance['tat_cl'] or "",
            "tat_dv": claim_instance['tat_dv'] or "",
            "circumstance": claim_instance['circumstance'],
            "date_dv_issued": claim_instance['date_dv_issued'].strftime('%Y-%m-%d') if claim_instance[
                'date_dv_issued'] else "",
            "dv_amount": claim_instance['dv_amount'] or "",
            "date_dv_returned": claim_instance['date_dv_returned'].strftime('%Y-%m-%d') if claim_instance[
                'date_dv_returned'] else "",
            "amount_paid": claim_instance['amount_paid'] or "",
            "created_at": claim_instance['created_at'].strftime('%Y-%m-%d') if claim_instance['created_at'] else "",
            "updated_at": claim_instance['updated_at'].strftime('%Y-%m-%d') if claim_instance['created_at'] else "",
            "registration_number": claim_instance['motor_details__registration_number'],
            "motor_class": claim_instance['motor_details__motor_class'],
            "assessor": claim_instance['motor_details__assessor'] or "",
            "days_pending": claim_instance['days_pending'] or "__Closed__",
            "status": "Closed"
        }

    elif claim_category == "Non_Motor":
        claim_instance = Claim.objects.with_days_pending().filter(status="Closed").select_related('non_motor_details').values(
            'documented', 'date_fully_documented', 'sub_status', 'notes', 'closure_date', 'tat_cl',
            'tat_dv', 'circumstance', 'date_dv_issued', 'dv_amount', 'date_dv_returned', 'dv_amount',
            'date_dv_returned', 'amount_paid', 'created_at', 'updated_at', 'non_motor_details__cover_type',
            'days_pending'
        ).get(id=claim_id)
        data = {
            "documented": "Yes" if claim_instance['documented'] else "No",
            "date_fully_documented": claim_instance['date_fully_documented'].strftime('%Y-%m-%d') if claim_instance[
                'date_fully_documented'] else "",
            "sub_status": claim_instance['sub_status'],
            "notes": claim_instance['notes'] or "",
            "closure_date": claim_instance['closure_date'].strftime('%Y-%m-%d') if claim_instance[
                'closure_date'] else "",
            "tat_cl": claim_instance['tat_cl'] or "",
            "tat_dv": claim_instance['tat_dv'] or "",
            "circumstance": claim_instance['circumstance'],
            "date_dv_issued": claim_instance['date_dv_issued'].strftime('%Y-%m-%d') if claim_instance[
                'date_dv_issued'] else "",
            "dv_amount": claim_instance['dv_amount'] or "",
            "date_dv_returned": claim_instance['date_dv_returned'].strftime('%Y-%m-%d') if claim_instance[
                'date_dv_returned'] else "",
            "amount_paid": claim_instance['amount_paid'] or "",
            "created_at": claim_instance['created_at'].strftime('%Y-%m-%d') if claim_instance['created_at'] else "",
            "updated_at": claim_instance['updated_at'].strftime('%Y-%m-%d') if claim_instance['updated_at'] else "",
            "days_pending": claim_instance['days_pending'] or "__Closed__",
            "cover_type": claim_instance['non_motor_details__cover_type'] or "",
            "status": "Closed"
        }

    elif claim_category == "Credit_Life":
        claim_instance = Claim.objects.with_days_pending().filter(status="Closed").select_related('credit_life_details').values(
            'documented', 'date_fully_documented', 'sub_status', 'notes', 'closure_date', 'tat_cl',
            'tat_dv', 'circumstance', 'date_dv_issued', 'dv_amount', 'date_dv_returned', 'dv_amount',
            'date_dv_returned', 'amount_paid', 'created_at', 'updated_at', 'credit_life_details__claim_trigger',
            'days_pending'
        ).get(id=claim_id)
        data = {
            "documented": "Yes" if claim_instance['documented'] else "No",
            "date_fully_documented": claim_instance['date_fully_documented'].strftime('%Y-%m-%d') if claim_instance[
                'date_fully_documented'] else "",

            "sub_status": claim_instance['sub_status'],
            "notes": claim_instance['notes'] or "",
            "closure_date": claim_instance['closure_date'].strftime('%Y-%m-%d') if claim_instance[
                'closure_date'] else "",
            "tat_cl": claim_instance['tat_cl'] or "",
            "tat_dv": claim_instance['tat_dv'] or "",
            "circumstance": claim_instance['circumstance'],
            "date_dv_issued": claim_instance['date_dv_issued'].strftime('%Y-%m-%d') if claim_instance[
                'date_dv_issued'] else "",
            "dv_amount": claim_instance['dv_amount'] or "",
            "date_dv_returned": claim_instance['date_dv_returned'].strftime('%Y-%m-%d') if claim_instance[
                'date_dv_returned'] else "",
            "amount_paid": claim_instance['amount_paid'] or "",
            "created_at": claim_instance['created_at'].strftime('%Y-%m-%d') if claim_instance['created_at'] else "",
            "updated_at": claim_instance['updated_at'].strftime('%Y-%m-%d') if claim_instance['updated_at'] else "",
            "claim_trigger": claim_instance['credit_life_details__claim_trigger'],
            "days_pending": claim_instance['days_pending'] or "__Closed__",
            "status": "Closed"
        }

    else:
        return JsonResponse({"error": "Invalid Category!"}, status=400)

    return JsonResponse(data, safe=False)

@login_required(login_url='login_page')
@require_GET
def total_claims_details_one(request, claim_id, claim_category):
    if claim_category == "Motor":
        claim_instance = Claim.objects.with_days_pending().select_related('motor_details').values(
            'documented', 'date_fully_documented', 'sub_status', 'notes', 'closure_date','tat_cl',
            'tat_dv','circumstance','date_dv_issued', 'dv_amount', 'date_dv_returned','dv_amount',
            'date_dv_returned','amount_paid','created_at','updated_at','motor_details__registration_number',
            'motor_details__motor_class','motor_details__assessor', 'days_pending', 'status'
        ).get(id=claim_id)
        data = {
            "documented": "Yes" if claim_instance['documented'] else "No",
            "date_fully_documented": claim_instance['date_fully_documented'].strftime('%Y-%m-%d')  if claim_instance["date_fully_documented"] else "",
            "sub_status": claim_instance['sub_status'],
            "notes": claim_instance['notes'] or "",
            "closure_date": claim_instance['closure_date'].strftime('%Y-%m-%d') if claim_instance['closure_date'] else "",
            "tat_cl": claim_instance['tat_cl'] or "",
            "tat_dv": claim_instance['tat_dv'] or "",
            "circumstance": claim_instance['circumstance'],
            "date_dv_issued": claim_instance['date_dv_issued'].strftime('%Y-%m-%d') if claim_instance['date_dv_issued'] else "",
            "dv_amount": claim_instance['dv_amount'] or "",
            "date_dv_returned": claim_instance['date_dv_returned'].strftime('%Y-%m-%d') if claim_instance['date_dv_returned'] else "",
            "amount_paid": claim_instance['amount_paid'] or "",
            "created_at": claim_instance['created_at'].strftime('%Y-%m-%d') if claim_instance['created_at'] else "",
            "updated_at": claim_instance['updated_at'].strftime('%Y-%m-%d') if claim_instance['created_at'] else "",
            "registration_number": claim_instance['motor_details__registration_number'],
            "motor_class": claim_instance['motor_details__motor_class'],
            "assessor": claim_instance['motor_details__assessor'] or "",
            "days_pending": claim_instance['days_pending'] or "__Closed__",
            "status": claim_instance['status']
        }

    elif claim_category == "Non_Motor":
        claim_instance = Claim.objects.with_days_pending().select_related('non_motor_details').values(
            'documented', 'date_fully_documented', 'sub_status', 'notes', 'closure_date', 'tat_cl',
            'tat_dv', 'circumstance', 'date_dv_issued', 'dv_amount', 'date_dv_returned', 'dv_amount',
            'date_dv_returned', 'amount_paid', 'created_at', 'updated_at', 'non_motor_details__cover_type', 'days_pending', 'status'
        ).get(id=claim_id)
        data = {
            "documented": "Yes" if claim_instance['documented'] else "No",
            "date_fully_documented": claim_instance['date_fully_documented'].strftime('%Y-%m-%d') if claim_instance['date_fully_documented'] else "",
            "sub_status": claim_instance['sub_status'],
            "notes": claim_instance['notes'] or "",
            "closure_date": claim_instance['closure_date'].strftime('%Y-%m-%d')  if claim_instance['closure_date'] else "",
            "tat_cl": claim_instance['tat_cl'] or "",
            "tat_dv": claim_instance['tat_dv'] or "",
            "circumstance": claim_instance['circumstance'],
            "date_dv_issued": claim_instance['date_dv_issued'].strftime('%Y-%m-%d') if claim_instance['date_dv_issued'] else "",
            "dv_amount": claim_instance['dv_amount'] or "",
            "date_dv_returned": claim_instance['date_dv_returned'].strftime('%Y-%m-%d')  if claim_instance['date_dv_returned'] else "",
            "amount_paid": claim_instance['amount_paid'] or "",
            "created_at": claim_instance['created_at'].strftime('%Y-%m-%d') if claim_instance['created_at'] else "",
            "updated_at": claim_instance['updated_at'] .strftime('%Y-%m-%d') if claim_instance['updated_at'] else "",
            "days_pending": claim_instance['days_pending'] or "__Closed__",
            "cover_type": claim_instance['non_motor_details__cover_type'] or "",
            "status": claim_instance['status']
        }

    elif claim_category == "Credit_Life":
        claim_instance = Claim.objects.with_days_pending().select_related('credit_life_details').values(
            'documented', 'date_fully_documented', 'sub_status', 'notes', 'closure_date', 'tat_cl',
            'tat_dv', 'circumstance', 'date_dv_issued', 'dv_amount', 'date_dv_returned', 'dv_amount',
            'date_dv_returned', 'amount_paid', 'created_at', 'updated_at', 'credit_life_details__claim_trigger', 'days_pending', 'status'
        ).get(id=claim_id)
        data = {
            "documented": "Yes" if claim_instance['documented'] else "No",
            "date_fully_documented": claim_instance['date_fully_documented'].strftime('%Y-%m-%d') if claim_instance['date_fully_documented'] else "",

            "sub_status": claim_instance['sub_status'],
            "notes": claim_instance['notes']or "" ,
            "closure_date": claim_instance['closure_date'].strftime('%Y-%m-%d') if claim_instance['closure_date'] else "",
            "tat_cl": claim_instance['tat_cl'] or "",
            "tat_dv": claim_instance['tat_dv'] or "",
            "circumstance": claim_instance['circumstance'],
            "date_dv_issued": claim_instance['date_dv_issued'].strftime('%Y-%m-%d') if claim_instance['date_dv_issued'] else "",
            "dv_amount": claim_instance['dv_amount'] or "",
            "date_dv_returned": claim_instance['date_dv_returned'].strftime('%Y-%m-%d')if claim_instance['date_dv_returned'] else "",
            "amount_paid": claim_instance['amount_paid'] or "",
            "created_at": claim_instance['created_at'].strftime('%Y-%m-%d') if claim_instance['created_at'] else "",
            "updated_at": claim_instance['updated_at'].strftime('%Y-%m-%d') if claim_instance['updated_at'] else "",
            "claim_trigger": claim_instance['credit_life_details__claim_trigger'],
            "days_pending": claim_instance['days_pending'] or "__Closed__",
            "status": claim_instance['status']
        }

    else:
        return JsonResponse({"error": "Invalid Category!"}, status=400)

    return JsonResponse(data, safe=False)





@login_required(login_url='login_page')
@require_POST
def total_claims(request):
    COLUMNS_ORDER_MAP = {
        0: "name_of_insured",
        1: "status",
        2: "category",
        3: "underwriter",
        4: "intimation_date",
        5: "date_of_loss",  # <<<<<<-
        6: "handler",
        7: "branch",
        8: "sum_insured",
    }

    try:
        draw = int(request.POST.get('draw', 1))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 100))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid pagination parameters"}, status=400)
    start = max(start, 0)
    length = min(max(length, 1), 500)  # cap page size to prevent abuse

    search_value = request.POST.get('search[value]', '').strip()

    try:
        order_column_index = int(request.POST.get('order[0][column]', 0))
    except (TypeError, ValueError):
        order_column_index = 0

    order_direction=request.POST.get('order[0][dir]', 'asc')
    order_field=COLUMNS_ORDER_MAP.get(order_column_index, "intimation_date")

    if order_direction == 'desc':
        order_field=f'-{order_field}'

    handler_filter=request.POST.get('handler', '').strip()
    category_filter = request.POST.get('category', '').strip()
    underwriter_filter = request.POST.get('underwriter', '').strip()
    status_filter = request.POST.get('status', '').strip()
    branch_filter=request.POST.get('branch', '').strip()

    base_qs=Claim.objects.with_days_pending().all()
    total_pending_claims=base_qs.count()

    filtered_qs=base_qs

    if handler_filter:
        filtered_qs=filtered_qs.filter(handler=handler_filter)
    if category_filter:
        filtered_qs=filtered_qs.filter(category=category_filter)
    if underwriter_filter:
        filtered_qs=filtered_qs.filter(underwriter=underwriter_filter)
    if status_filter:
        filtered_qs=filtered_qs.filter(status=status_filter)
    if branch_filter:
        filtered_qs=filtered_qs.filter(branch=branch_filter)

    if search_value:
        filtered_qs=filtered_qs.filter(name_of_insured__icontains=search_value)

    records_filtered=filtered_qs.count()

    page_qs = filtered_qs.values(
    'id', 'name_of_insured', 'status', 'category', 'underwriter',
    'intimation_date', 'date_of_loss', 'handler', 'branch',
    'sum_insured').order_by(order_field)[start:start+length]

    data=[]

    for claim in page_qs:
        data.append({
            "id": claim['id'],
            "name_of_insured": claim['name_of_insured'],
            "status" : claim['status'],
            "category": claim['category'],
            "underwriter": claim['underwriter'],
            "intimation_date": claim['intimation_date'].strftime("%Y-%m-%d") if claim['intimation_date'] else "",
            "date_of_loss": claim['date_of_loss'].strftime("%Y-%m-%d") if claim['date_of_loss'] else "",
            "handler": claim['handler'],
            "branch": claim['branch'],
            "sum_insured": claim['sum_insured'],
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_pending_claims,
        "recordsFiltered": records_filtered,
        "data": data,
    })

@login_required(login_url='login_page')
@require_POST
def closed_claims(request):
    COLUMNS_ORDER_MAP = {
        0: "name_of_insured",
        1: "category",
        2: "underwriter",
        3: "intimation_date",
        4: "date_of_loss",
        5: "handler",
        6: "branch",
        7: "sum_insured",
        8: "sub_status",
        9: "amount_paid",
        10: "id"

    }

    try:
        draw = int(request.POST.get('draw', 1))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 100))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid pagination parameters"}, status=400)
    start = max(start, 0)
    length = min(max(length, 1), 500)  # cap page size to prevent abuse

    search_value = request.POST.get('search[value]', '').strip()

    try:
        order_column_index = int(request.POST.get('order[0][column]', 0))
    except (TypeError, ValueError):
        order_column_index = 0

    order_direction=request.POST.get('order[0][dir]', 'asc')
    order_field=COLUMNS_ORDER_MAP.get(order_column_index, "intimation_date")

    if order_direction == 'desc':
        order_field=f'-{order_field}'

    handler_filter=request.POST.get('handler', '').strip()
    category_filter = request.POST.get('category', '').strip()
    underwriter_filter = request.POST.get('underwriter', '').strip()
    sub_status_filter = request.POST.get('subStatus', '').strip()
    branch_filter=request.POST.get('branch', '').strip()

    base_qs=Claim.objects.with_days_pending().filter(status='Closed')
    total_pending_claims=base_qs.count()

    filtered_qs=base_qs

    if handler_filter:
        filtered_qs=filtered_qs.filter(handler=handler_filter)
    if category_filter:
        filtered_qs=filtered_qs.filter(category=category_filter)
    if underwriter_filter:
        filtered_qs=filtered_qs.filter(underwriter=underwriter_filter)
    if sub_status_filter:
        filtered_qs=filtered_qs.filter(sub_status=sub_status_filter)
    if branch_filter:
        filtered_qs=filtered_qs.filter(branch=branch_filter)

    if search_value:
        filtered_qs=filtered_qs.filter(name_of_insured__icontains=search_value)

    records_filtered=filtered_qs.count()

    page_qs = filtered_qs.values(
    'name_of_insured', 'category', 'underwriter',
    'intimation_date', 'date_of_loss', 'handler', 'branch',
    'sum_insured', 'sub_status', 'amount_paid', 'id').order_by(order_field)[start:start+length]

    data=[]

    for claim in page_qs:
        data.append({
            "name_of_insured": claim['name_of_insured'],
            "category": claim['category'],
            "underwriter": claim['underwriter'],
            "intimation_date": claim['intimation_date'].strftime("%Y-%m-%d") if claim['intimation_date'] else "",
            "date_of_loss": claim['date_of_loss'].strftime("%Y-%m-%d") if claim['date_of_loss'] else "",
            "handler": claim['handler'],
            "branch": claim['branch'],
            "sum_insured": claim['sum_insured'],
            "sub_status" : claim['sub_status'],
            "amount_paid" : claim['amount_paid'],
            "id": claim['id']
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_pending_claims,
        "recordsFiltered": records_filtered,
        "data": data,
    })

@login_required(login_url='login_page')
@require_POST
def pending_claims(request):
    COLUMNS_ORDER_MAP = {
        0: "name_of_insured",
        1: "category",
        2: "underwriter",
        3: "intimation_date",
        4: "date_of_loss",
        5: "days_pending",
        6: "documented",
        7: "date_fully_documented",
        8: "handler",
        9: "branch",
        10: "sub_status",
        11: "sum_insured",
        12: "id"
    }

    try:
        draw = int(request.POST.get('draw', 1))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 100))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid pagination parameters"}, status=400)
    start = max(start, 0)
    length = min(max(length, 1), 500)  # cap page size to prevent abuse

    search_value = request.POST.get('search[value]', '').strip()

    try:
        order_column_index = int(request.POST.get('order[0][column]', 0))
    except (TypeError, ValueError):
        order_column_index = 0

    order_direction=request.POST.get('order[0][dir]', 'asc')
    order_field=COLUMNS_ORDER_MAP.get(order_column_index, "intimation_date")

    if order_direction == 'desc':
        order_field=f'-{order_field}'

    handler_filter=request.POST.get('handler', '').strip()
    category_filter = request.POST.get('category', '').strip()
    underwriter_filter = request.POST.get('underwriter', '').strip()
    sub_status_filter = request.POST.get('subStatus', '').strip()
    branch_filter=request.POST.get('branch', '').strip()

    base_qs=Claim.objects.with_days_pending().filter(status='Pending')
    total_pending_claims=base_qs.count()

    filtered_qs=base_qs

    if handler_filter:
        filtered_qs=filtered_qs.filter(handler=handler_filter)
    if category_filter:
        filtered_qs=filtered_qs.filter(category=category_filter)
    if underwriter_filter:
        filtered_qs=filtered_qs.filter(underwriter=underwriter_filter)
    if sub_status_filter:
        filtered_qs=filtered_qs.filter(sub_status=sub_status_filter)
    if branch_filter:
        filtered_qs=filtered_qs.filter(branch=branch_filter)

    if search_value:
        filtered_qs=filtered_qs.filter(name_of_insured__icontains=search_value)

    records_filtered=filtered_qs.count()

    page_qs = filtered_qs.values(
    'name_of_insured', 'category', 'underwriter',
    'intimation_date', 'date_of_loss', 'days_pending',
    'documented','date_fully_documented', 'handler', 'branch',
    'sub_status', 'sum_insured', 'id').order_by(order_field)[start:start+length]

    data=[]

    for claim in page_qs:
        data.append({
            "name_of_insured": claim['name_of_insured'],
            "category": claim['category'],
            "underwriter": claim['underwriter'],
            "intimation_date": claim['intimation_date'].strftime("%Y-%m-%d") if claim['intimation_date'] else "",
            "date_of_loss": claim['date_of_loss'].strftime("%Y-%m-%d") if claim['date_of_loss'] else "",
            "days_pending": claim["days_pending"],
            "documented": claim["documented"],
            "date_fully_documented": claim["date_fully_documented"],
            "handler": claim['handler'],
            "branch": claim['branch'],
            "sub_status": claim["sub_status"],
            "sum_insured": claim['sum_insured'],
            "id": claim['id']

        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_pending_claims,
        "recordsFiltered": records_filtered,
        "data": data,
    })






@login_required(login_url='login_page')
@require_POST
def all_pending_claims(request):
    COLUMNS_ORDER_MAP = {
        0: "name_of_insured",
        1: "category",
        2: "underwriter",
        3: "intimation_date",
        4: "date_of_loss",
        5: "days_pending",  # <<<<<<-
        6: "documented",
        7: "date_fully_documented",
        8: "handler",
        9: "sub_status",  # <<<<<<<-
        10: "branch",
    }

    try:
        draw = int(request.POST.get('draw', 1))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 100))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid pagination parameters"}, status=400)
    start = max(start, 0)
    length = min(max(length, 1), 500)  # cap page size to prevent abuse

    search_value = request.POST.get('search[value]', '').strip()

    try:
        order_column_index = int(request.POST.get('order[0][column]', 0))
    except (TypeError, ValueError):
        order_column_index = 0

    order_direction=request.POST.get('order[0][dir]', 'asc')
    order_field=COLUMNS_ORDER_MAP.get(order_column_index, "intimation_date")

    if order_direction == 'desc':
        order_field=f'-{order_field}'

    handler_filter=request.POST.get('handler', '').strip()
    sub_status_filter=request.POST.get('sub_status', '').strip()
    branch_filter=request.POST.get('branch', '').strip()

    base_qs=Claim.objects.with_days_pending().filter(status='Pending')
    total_pending_claims=base_qs.count()

    filtered_qs=base_qs

    if handler_filter:
        filtered_qs=filtered_qs.filter(handler=handler_filter)
    if sub_status_filter:
        filtered_qs=filtered_qs.filter(sub_status=sub_status_filter)
    if branch_filter:
        filtered_qs=filtered_qs.filter(branch=branch_filter)

    if search_value:
        filtered_qs=filtered_qs.filter(name_of_insured__icontains=search_value)

    records_filtered=filtered_qs.count()

    page_qs = filtered_qs.values(
    'name_of_insured', 'category', 'underwriter', 'intimation_date',
    'date_of_loss', 'documented', 'date_fully_documented',
    'handler', 'sub_status', 'branch', 'days_pending', 'sum_insured'
            ).order_by(order_field)[start:start+length]

    data=[]

    for claim in page_qs:
        data.append({
            "name_of_insured": claim['name_of_insured'],
            "category": claim['category'],
            "underwriter": claim['underwriter'],
            "intimation_date": claim['intimation_date'].strftime("%Y-%m-%d") if claim['intimation_date'] else "",
            "date_of_loss": claim['date_of_loss'].strftime("%Y-%m-%d") if claim['date_of_loss'] else "",
            "days_pending": claim['days_pending'],
            "documented": ("Yes" if claim['documented'] else "No"),
            "date_fully_documented": (claim['date_fully_documented'].strftime("%Y-%m-%d") if claim['date_fully_documented'] else ""),
            "handler": claim['handler'],
            "sub_status": claim['sub_status'],
            "branch": claim['branch'],
            "sum_insured": claim['sum_insured'],
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_pending_claims,
        "recordsFiltered": records_filtered,
        "data": data,
    })

@login_required(login_url='login_page')
@require_POST
def pending_motor_claims(request):
    COLUMNS_ORDER_MAP = {
        0: "id",
        1: "name_of_insured",
        2: "motor_details__registration_number",
        3: "motor_details__motor_class",
        4: "circumstance",
        5: "intimation_date",
        6: "date_of_loss",
        7: "handler",
        8: "days_pending",
        9: "underwriter",
        10: "documented",
        11: "date_fully_documented",
        12: "sub-status",
        13: "branch"
    }

    try:
        draw = int(request.POST.get('draw', 1))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 100))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid pagination parameters"}, status=400)
    start = max(start, 0)
    length = min(max(length, 1), 500)  # cap page size to prevent abuse

    search_value = request.POST.get('search[value]', '').strip()

    try:
        order_column_index = int(request.POST.get('order[0][column]', 0))
    except (TypeError, ValueError):
        order_column_index = 0

    order_direction = request.POST.get('order[0][dir]', 'asc')
    order_field = COLUMNS_ORDER_MAP.get(order_column_index, "intimation_date")

    if order_direction == 'desc':
        order_field = f'-{order_field}'

    handler_filter = request.POST.get('handler', '').strip()
    sub_status_filter=request.POST.get('sub_status', '').strip()
    branch_filter = request.POST.get('branch', '').strip()

    base_pending_motor_qs = Claim.objects.with_days_pending().select_related('motor_details').filter(status='Pending', category='Motor')
    total_pending_motor_claims = base_pending_motor_qs.count()

    filtered_qs = base_pending_motor_qs

    if handler_filter:
        filtered_qs = filtered_qs.filter(handler=handler_filter)
    if sub_status_filter:
        filtered_qs=filtered_qs.filter(sub_status=sub_status_filter)
    if branch_filter:
        filtered_qs = filtered_qs.filter(branch=branch_filter)

    if search_value:
        filtered_qs = filtered_qs.filter(
            Q(motor_details__registration_number__icontains=search_value) |
            Q(name_of_insured__icontains=search_value)
        )

    records_filtered = filtered_qs.count()

    page_qs = filtered_qs.values(
        'id','name_of_insured','motor_details__registration_number','motor_details__motor_class',
        'circumstance','intimation_date','date_of_loss','handler',
        'underwriter','documented','date_fully_documented','sub_status','branch', 'days_pending'
    ).order_by(order_field)[start:start + length]

    data = []

    for claim in page_qs:
        data.append({
            "id": claim['id'],
            "name_of_insured": claim['name_of_insured'],
            "registration_number": claim.get('motor_details__registration_number', ''),
            "motor_class": claim.get('motor_details__motor_class', ''),
            "circumstance": claim['circumstance'],
            "intimation_date": claim['intimation_date'].strftime("%Y-%m-%d") if claim['intimation_date'] else "",
            "date_of_loss": claim['date_of_loss'].strftime("%Y-%m-%d") if claim['date_of_loss'] else "",
            "handler": claim['handler'],
            "days_pending": claim['days_pending'],
            "underwriter": claim['underwriter'],
            "documented": claim['documented'],
            "date_fully_documented": (claim['date_fully_documented'].strftime("%Y-%m-%d") if claim['date_fully_documented'] else ""),
            "sub_status": claim['sub_status'],
            "branch": claim['branch'],
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_pending_motor_claims,
        "recordsFiltered": records_filtered,
        "data": data,
    })

@login_required(login_url='login_page')
@require_GET
def motor_claim_details_one(request, claim_id):
    try:
        claim = (Claim.objects.select_related('motor_details').values(
            # 'supporting_documents', 'supporting_images',
            'motor_details__assessor',
            'notes', 'sum_insured', 'dv_amount',
            'date_dv_issued', 'date_dv_returned',
            'closure_date', 'updated_at'
        ).get(pk=claim_id))

    except Claim.DoesNotExist:
        return JsonResponse({"error": "claim was not found"}, status=404)

    data = {
        "assessor": claim.get('motor_details__assessor', ""),
        "notes": claim['notes'] or "",
        "sum_insured": claim['sum_insured'] or "",
        "dv_amount": claim['dv_amount'] or "",
        "date_dv_issued": claim['date_dv_issued'].strftime("%Y-%m-%d") if claim[
        'date_dv_issued'] else "",
        "date_dv_returned": claim['date_dv_returned'].strftime("%Y-%m-%d") if claim[
        'date_dv_returned'] else "",
        "closure_date": claim['closure_date'].strftime("%Y-%m-%d") if claim['closure_date'] else "",
        "last_updated_at": claim['updated_at'] if claim['updated_at'] else None
    }
    return JsonResponse(data, safe=False)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_new_claim(request):
    category = request.data.get('category')

    if category == 'Motor':
        serializer = ClaimMotorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201, safe=False)
        return JsonResponse(serializer.errors, status=400, safe=False)

    elif category == 'Non_Motor':
        serializer = ClaimNon_MotorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201, safe=False)
        return JsonResponse(serializer.errors, status=400, safe=False)

    elif category == 'Credit_Life':
        serializer = ClaimCredit_LifeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201, safe=False)
        return JsonResponse(serializer.errors, status=400, safe=False)

    else:
        return JsonResponse({"error": f"Category - { category } not supported"}, status=400, safe=False)



@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_claim (request, pk):
    category = request.data.get('category')

    if category == 'Motor':
        try:
            claim = Claim.objects.select_related('motor_details').get(pk=pk)

        except Claim.DoesNotExist:
            return JsonResponse({"error": f"claim no.{pk} was not found"}, status=400)

        serializer = ClaimMotorSerializer(
            instance=claim,  # ← existing object
            data=request.data,
            partial=True   # ← important for PATCH
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif category == 'Non_Motor':
        try:
            claim = Claim.objects.select_related('non_motor_details').get(pk=pk)

        except Claim.DoesNotExist:
            return JsonResponse({"error": f"claim no.{pk} was not found"}, status=400)

        serializer = ClaimNon_MotorSerializer(
            instance=claim,  # ← existing object
            data=request.data,
            partial=True  # ← important for PATCH
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif category == 'Credit_Life':
        try:
            claim = Claim.objects.select_related('credit_life_details').get(pk=pk)

        except Claim.DoesNotExist:
            return JsonResponse({"error": f"claim no.{pk} was not found"}, status=400)

        serializer = ClaimCredit_LifeSerializer(
            instance=claim,  # ← existing object
            data=request.data,
            partial=True  # ← important for PATCH
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    else:
        return JsonResponse({"error": "Invalid Category"}, status=400)

@login_required(login_url='login_page')
@require_POST
def pending_non_motor_claims(request):
    COLUMNS_ORDER_MAP ={
        0: "id",
        1: "name_of_insured",
        2: "non_motor_details__cover_type",
        3: "circumstance",
        4: "intimation_date",
        5: "date_of_loss",
        6: "handler",
        7: "days_pending",
        8: "underwriter",
        9: "documented",
        10: "date_fully_documented",
        11: "sub_status",
        12: "branch",
        13: "sum_insured",

    }

    try:
        draw = int(request.POST.get('draw', 1))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 100))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid pagination parameters"}, status=400)
    start = max(start, 0)
    length = min(max(length, 1), 500)  # cap page size to prevent abuse

    search_value = request.POST.get('search[value]', '').strip()

    try:
        order_column_index = int(request.POST.get('order[0][column]', 0))
    except (TypeError, ValueError):
        order_column_index = 0

    order_direction = request.POST.get('order[0][dir]', 'asc')
    order_field = COLUMNS_ORDER_MAP.get(order_column_index, "intimation_date")

    if order_direction == 'desc':
        order_field = f'-{order_field}'

    handler_filter = request.POST.get('handler', '').strip()
    sub_status_filter=request.POST.get('sub_status', '').strip()
    branch_filter = request.POST.get('branch', '').strip()

    base_pending_non_motor_qs = Claim.objects.with_days_pending().select_related('non_motor_details').filter(status='Pending', category='Non_Motor')
    total_pending_non_motor_claims = base_pending_non_motor_qs.count()

    filtered_qs = base_pending_non_motor_qs

    if handler_filter:
        filtered_qs = filtered_qs.filter(handler=handler_filter)
    if sub_status_filter:
        filtered_qs=filtered_qs.filter(sub_status=sub_status_filter)
    if branch_filter:
        filtered_qs = filtered_qs.filter(branch=branch_filter)
    if search_value:
        filtered_qs = filtered_qs.filter(
            Q(name_of_insured__icontains=search_value)
        )

    records_filtered = filtered_qs.count()

    page_qs = filtered_qs.values(
                "id",
                "name_of_insured",
                "non_motor_details__cover_type",
                "circumstance",
                "intimation_date",
                "date_of_loss",
                "handler",
                "days_pending",
                "underwriter",
                "documented",
                "date_fully_documented",
                "sub_status",
                "branch",
                "sum_insured",
    ).order_by(order_field)[start:start + length]

    data = []

    for claim in page_qs:
        data.append({
            "id": claim["id"],
            "name_of_insured": claim["name_of_insured"],
            "cover_type": claim.get("non_motor_details__cover_type"),
            "circumstance": claim["circumstance"],
            "intimation_date": claim["intimation_date"].strftime("%Y-%m-%d") if claim["intimation_date"] else "",
            "date_of_loss": claim["date_of_loss"].strftime("%Y-%m-%d") if claim["date_of_loss"] else "",
            "handler": claim["handler"],
            "days_pending": claim["days_pending"] if claim["days_pending"] else "",
            "underwriter": claim["underwriter"],
            "documented": claim["documented"],
            "date_fully_documented": (claim["date_fully_documented"].strftime("%Y-%m-%d") if claim["date_fully_documented"] else ""),
            "sub_status": claim["sub_status"],
            "branch": claim["branch"],
            "sum_insured": claim["sum_insured"]
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_pending_non_motor_claims,
        "recordsFiltered": records_filtered,
        "data": data,
    })

@login_required(login_url='login_page')
@require_GET
def non_motor_claim_details_one(request, claim_id):
    try:
        claim = (Claim.objects.select_related('non_motor_details').values(
            'notes', 'dv_amount',
            'date_dv_issued', 'date_dv_returned',
            'closure_date', 'updated_at'
        ).get(pk=claim_id))

    except Claim.DoesNotExist:
        return JsonResponse({"error": "claim was not found"}, status=404)

    data = {
        "notes": claim['notes'] or "",
        "dv_amount": claim['dv_amount'] or "",
        "date_dv_issued": claim['date_dv_issued'].strftime("%Y-%m-%d") if claim[
        'date_dv_issued'] else "",
        "date_dv_returned": claim['date_dv_returned'].strftime("%Y-%m-%d") if claim[
        'date_dv_returned'] else "",
        "closure_date": claim['closure_date'].strftime("%Y-%m-%d") if claim['closure_date'] else "",
        "last_updated_at": claim['updated_at'] if claim['updated_at'] else None
    }
    return JsonResponse(data, safe=False)


@login_required(login_url='login_page')
@require_POST
def pending_credit_life_claims(request):
    COLUMNS_ORDER_MAP = {
        0: "id",
        1: "name_of_insured",
        2: "credit_life_details__claim_trigger",
        3: "circumstance",
        4: "intimation_date",
        5: "date_of_loss",
        6: "handler",
        7: "days_pending",
        8: "underwriter",
        9: "documented",
        10: "date_fully_documented",
        11: "sub_status",
        12: "branch",
        13: "sum_insured",

    }

    try:
        draw = int(request.POST.get('draw', 1))
        start = int(request.POST.get('start', 0))
        length = int(request.POST.get('length', 100))
    except (TypeError, ValueError):
        return JsonResponse({"error": "Invalid pagination parameters"}, status=400)
    start = max(start, 0)
    length = min(max(length, 1), 500)  # cap page size to prevent abuse

    search_value = request.POST.get('search[value]', '').strip()

    try:
        order_column_index = int(request.POST.get('order[0][column]', 0))
    except (TypeError, ValueError):
        order_column_index = 0

    order_direction = request.POST.get('order[0][dir]', 'asc')
    order_field = COLUMNS_ORDER_MAP.get(order_column_index, "intimation_date")

    if order_direction == 'desc':
        order_field = f'-{order_field}'

    handler_filter = request.POST.get('handler', '').strip()
    sub_status_filter = request.POST.get('sub_status', '').strip()
    branch_filter = request.POST.get('branch', '').strip()

    base_pending_credit_life_qs = Claim.objects.with_days_pending().select_related('credit_life_details').filter(
        status='Pending', category='Credit_Life'
            )
    total_pending_credit_life_claims = base_pending_credit_life_qs.count()

    filtered_qs = base_pending_credit_life_qs

    if handler_filter:
        filtered_qs = filtered_qs.filter(handler=handler_filter)
    if sub_status_filter:
        filtered_qs = filtered_qs.filter(sub_status=sub_status_filter)
    if branch_filter:
        filtered_qs = filtered_qs.filter(branch=branch_filter)
    if search_value:
        filtered_qs = filtered_qs.filter(
            Q(name_of_insured__icontains=search_value)
        )

    records_filtered = filtered_qs.count()

    page_qs = filtered_qs.values(
        "id",
        "name_of_insured",
        "credit_life_details__claim_trigger",
        "circumstance",
        "intimation_date",
        "date_of_loss",
        "handler",
        "days_pending",
        "underwriter",
        "documented",
        "date_fully_documented",
        "sub_status",
        "branch",
        "sum_insured",
    ).order_by(order_field)[start:start + length]

    data = []

    for claim in page_qs:
        data.append({
            "id": claim["id"],
            "name_of_insured": claim["name_of_insured"],
            "claim_trigger": claim.get("credit_life_details__claim_trigger"),
            "circumstance": claim["circumstance"],
            "intimation_date": claim["intimation_date"].strftime("%Y-%m-%d") if claim["intimation_date"] else "",
            "date_of_loss": claim["date_of_loss"].strftime("%Y-%m-%d") if claim["date_of_loss"] else "",
            "handler": claim["handler"],
            "days_pending": claim["days_pending"] if claim["days_pending"] else "",
            "underwriter": claim["underwriter"],
            "documented": claim["documented"],
            "date_fully_documented": (
                claim["date_fully_documented"].strftime("%Y-%m-%d") if claim["date_fully_documented"] else ""),
            "sub_status": claim["sub_status"],
            "branch": claim["branch"],
            "sum_insured": claim["sum_insured"]
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total_pending_credit_life_claims,
        "recordsFiltered": records_filtered,
        "data": data,
    })

@login_required(login_url='login_page')
@require_GET
def credit_life_claim_details_one(request, claim_id):
    try:
        claim = Claim.objects.select_related('credit_life_details').values(
            'notes', 'dv_amount',
            'date_dv_issued', 'date_dv_returned',
            'closure_date', 'updated_at'
        ).get(pk=claim_id)

    except Claim.DoesNotExist:
        return JsonResponse({"error": "claim was not found"}, status=404)

    data = {
        "notes": claim['notes'] or "",
        "dv_amount": claim['dv_amount'] or "",
        "date_dv_issued": claim['date_dv_issued'].strftime("%Y-%m-%d") if claim[
        'date_dv_issued'] else "",
        "date_dv_returned": claim['date_dv_returned'].strftime("%Y-%m-%d") if claim[
        'date_dv_returned'] else "",
        "closure_date": claim['closure_date'].strftime("%Y-%m-%d") if claim['closure_date'] else "",
        "last_updated_at": claim['updated_at'] if claim['updated_at'] else None
    }
    return JsonResponse(data, safe=False)


# @require_GET
# def json_display(request):
#     claims = Claim.objects.select_related('motor_details').get(id=1)
#     serializers = ClaimMotorSerializer(claims)
#     return JsonResponse(serializers.data, safe=False)










#@api_view('GET')
# @permission_classes([IsAuthenticated])
# def api_reports_and_analysis_page(request):
#
#     # Executes EXACTLY ONE SQL query across the entire database table
#     underwriter_metrics = Claim.objects.values('underwriter').annotate(
#         total_claims=Count('id'),
#         closed_claims=Count('id', filter=Q(status='Closed')),
#         pending_claims=Count('id', filter=Q(status='Pending')),
#         paid_claims=Count('id', filter=Q(sub_status='Paid')),
#         rejected_claims=Count('id', filter=Q(sub_status='Rejected')),
#         avg_tat=Avg('tat_dv', filter=Q(status='Closed'))
#     )
#
#     underwriter_data = []
#
#
#     for row in underwriter_metrics:
#         total = row['total_claims']
#
#         underwriter_data.append({
#             'underwriter_name': row['underwriter'],
#             'total_claims': total,
#             'closed_claims': row['closed_claims'],
#             'pending_claims': row['pending_claims'],
#             'settlement_ratio': round((row['paid_claims'] / row['closed_claims']) * 100, 2) if row['paid_claims'] > 0 and row['closed_claims'] > 0 else 0.0,
#             'average_tat_dv': round(row['avg_tat'], 1) if row['avg_tat'] is not None else 0.0,
#             'rejection_rate': round((row['rejected_claims'] / total) * 100, 2) if total > 0 else 0.0,
#         })
#
#     return JsonResponse(
#         underwriter_data,
#         safe=False
#     )
#







# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def add_new_claims_bulk(request):
#     """
#     Bulk-create claims for development/testing.
#     Expected body:
#     {
#         "category": "Motor",
#         "claims": [ {...}, {...}, ... ]
#     }
#     """
#     category = request.data.get('category')
#     claims_data = request.data.get('claims')
#
#     if not category:
#         return Response({"error": "category is required"}, status=status.HTTP_400_BAD_REQUEST)
#     if not claims_data or not isinstance(claims_data, list):
#         return Response({"error": "claims must be a non-empty list"}, status=status.HTTP_400_BAD_REQUEST)
#
#     serializer_map = {
#         'Motor': ClaimMotorSerializer,
#         'Non_Motor': ClaimNon_MotorSerializer,
#         'Credit_Life': ClaimCredit_LifeSerializer,
#     }
#
#     serializer_class = serializer_map.get(category)
#     if not serializer_class:
#         return Response({"error": "invalid category"}, status=status.HTTP_400_BAD_REQUEST)
#
#     # Ensure every item carries the category, since your models rely on it
#     for claim in claims_data:
#         claim['category'] = category
#
#     serializer = serializer_class(data=claims_data, many=True)
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from django.conf import settings


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_new_claims_bulk(request):
    if not settings.DEBUG:
        return Response({"error": "Not available outside DEBUG mode"}, status=status.HTTP_403_FORBIDDEN)

    claims_data = request.data
    if not isinstance(claims_data, list) or not claims_data:
        return Response(
            {"error": "Request body must be a non-empty list of claim objects"},
            status=status.HTTP_400_BAD_REQUEST
        )

    serializer_map = {
        'Motor': ClaimMotorSerializer,
        'Non_Motor': ClaimNon_MotorSerializer,
        'Credit_Life': ClaimCredit_LifeSerializer,
    }

    created = []
    errors = []

    for index, claim in enumerate(claims_data):
        category = claim.get('category')
        serializer_class = serializer_map.get(category)

        if not serializer_class:
            errors.append({
                "index": index,
                "claim_id": claim.get("claim_id"),
                "error": f"invalid category '{category}'",
            })
            continue

        # "claim_id" (e.g. "CLM-1001") is a seed-data label, not an actual model field
        claim_payload = {k: v for k, v in claim.items() if k != "claim_id"}

        serializer = serializer_class(data=claim_payload)
        if serializer.is_valid():
            serializer.save()
            created.append(serializer.data)
        else:
            errors.append({
                "index": index,
                "claim_id": claim.get("claim_id"),
                "errors": serializer.errors,
            })

    return Response(
        {"created_count": len(created), "created": len(created), "errors": errors},
        status=status.HTTP_201_CREATED if created else status.HTTP_400_BAD_REQUEST,
    )




@api_view (['POST'])
@permission_classes([IsAuthenticated])
def create_claim(request):
    if request.data.get('category') == 'Motor':
        serializer = ClaimMotorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.data.get('category') == 'Non_Motor':
        serializer = ClaimNon_MotorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    elif request.data.get('category') == 'Credit_Life':
        serializer = ClaimCredit_LifeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"error": "invalid category"}, status=status.HTTP_400_BAD_REQUEST)



# 2. View to serve JSON data for DataTables
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def view_claim_api(request):
    model = Claim.objects.filter(category='Motor')
    serializer = ClaimMotorSerializer(model, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_claim(request, search_value):
    results = Claim.objects.filter(name_of_insured__icontains=search_value)
    if not results.exists():
        return Response({"error": "claim with not found"}, status=status.HTTP_400_BAD_REQUEST)
    category=results.first().category

    if category == 'Motor':
        serializer = ClaimMotorSerializer(results, many=True)
        return Response(serializer.data)
    if category == 'Non_Motor':
        serializer= ClaimNon_MotorSerializer(results, many=True)
        return Response(serializer.data)
    if category == 'Credit_Life':
        serializer = ClaimCredit_LifeSerializer(results, many=True)
        return Response(serializer.data)
    else:
        return Response({"error": "invalid category"}, status=status.HTTP_400_BAD_REQUEST)





# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def view_claim(request):
#     model = Claim.objects.filter(category='Motor')
#     serializer = ClaimMotorSerializer(model, many=True)
#     # return render(request, 'all_pending_claims.html', { "claims": serializer.data})
#     return Response(serializer.data)









# @permission_classes([IsAuthenticated])
# @api_view(['GET', 'PATCH'])
# def update_claim(request, claim_id):
#     try:
#         claim = Claim.objects.get(pk=claim_id)
#     except Claim.DoesNotExist:
#         return Response({"error": "claim with not found"}, status=status.HTTP_404_NOT_FOUND)
#
#     # if request.method == 'GET':
#     #     serializer = ClaimCredit_LifeSerializer(claim)
#     #     return Response(serializer.data, status=status.HTTP_200_OK)
#
#     serializer = ClaimCredit_LifeSerializer(
#         instance = claim,  # ← existing object
#         data=request.data,
#         partial=True  # ← important for PATCH
#     )
#     if serializer.is_valid():
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_200_OK)
#     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

















