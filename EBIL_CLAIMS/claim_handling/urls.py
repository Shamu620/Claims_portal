from django.urls import path
from . import views

urlpatterns = [

    #pages
    path('', views.all_pending_claims_page, name='pending_claims_page'),
    path('pending-motor-claims/', views.motor_claims_pending_page, name='motor_claims_page'),
    path('pending-non-motor-claims/', views.non_motor_claims_pending_page, name='non_motor_claims_page' ),
    path('pending-credit-life-claims/', views.credit_life_claims_pending_page, name='credit_life_claims_page'),
    path('legal-claims/', views.legal_claims_page, name='legal_claims_page'),
    path('reports&analysis/underwriter-performance/', views.reports_underwriter_performance_page, name='reports_underwriter_performance_page'),
    path('report&analysis/claims-data', views.reports_claims_data_page, name='reports_claims_data_page'),
    path('reports&analysis/trends', views.reports_trends_page, name='reports_trends_page'),
    path('test-download/', views.export_csv_to_excel, name='test_download'),
    path('io-testing/', views.io_testing, name='io_testing'),







    #APIs
    path('api/all-pending-claims/', views.all_pending_claims, name='api_pending_claims'),
    path('api/pending-motor-claims/', views.pending_motor_claims, name='api_pending_motor_claims'),
    path('api/motor-claim-details-one/<int:claim_id>/', views.motor_claim_details_one, name='motor_claim_details_one'),
    path('api/update-claim/<int:pk>/', views.update_claim, name='update_claim'),
    path('api/add-new-claim/', views.add_new_claim, name='add_new_motor_claim'),
    path('api/pending-non-motor-claims/', views.pending_non_motor_claims, name='api_pending_non_motor_claims'),
    path('api/non-motor-claim-details-one/<int:claim_id>/', views.non_motor_claim_details_one, name='non_motor_claim_details_one'),
    path('api/pending-credit-life-claims/', views.pending_credit_life_claims, name='api_pending_life_claims'),
    path('api/credit-life-claim-details-one/<int:claim_id>/', views.credit_life_claim_details_one, name='credit_life_claim_details_one'),
    path('api/total-claims/', views.total_claims, name='total_claims_api'),
    path('api/closed-claims/', views.closed_claims, name='closed_claims_api'),
    path('api/pending-claims/', views.pending_claims, name='pending_claims_api'),
    path('api/download-total-claims/', views.download_total_claims, name='download_total_claims_api'),
    path('api/download-closed-claims/', views.download_closed_claims, name='download_closed_claims_api'),
    path('api/download-pending-claims/', views.download_pending_claims, name='download_pending_claims_api'),
    path('api/total-claims-details-one/<int:claim_id>/<str:claim_category>/', views.total_claims_details_one, name='total_claims_details_one'),
    path('api/closed-claims-details-one/<int:claim_id>/<str:claim_category>/', views.closed_claims_details_one, name='closed_claims_details_one'),
    path('api/pending-claims-details-one/<int:claim_id>/<str:claim_category>/', views.pending_claims_details_one,name='pending_claims_details_one'),
    # path('api/log-in/', views.log_in, name='log_in'),
    # path('test-email/', views.test_email_view, name='test_email'),


    # path('api/underwriter-data/', views.api_reports_and_analysis_page, name='underwriter_data'),
    # path('api/json_display', views.json_display, name='json_display'),

    # Route for the JSON API (called by fetch inside JavaScript)
    path('api/view_claims/', views.view_claim_api, name='view_claims'),
    path('create_claim/', views.create_claim, name='create_claim'),
    path('update_claim/<int:claim_id>/', views.update_claim, name='update_claim'),
    path('api/search_claim/<str:search_value>', views.search_claim, name='search_claim'),


    #Bulk addition of new claims
    path('add-bulk-instances/', views.add_new_claims_bulk, name='create_bulk_instances'),
]

