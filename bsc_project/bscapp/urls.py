from django.urls import path
from . import views

urlpatterns = [
    # TEMPORARY DIAGNOSTIC PATH (Do not remove)
    path('debug/templates/', views.diagnostic_view, name='diagnostic_view'),

    # Main page - maps to http://127.0.0.1:8000/
    path('', views.index, name='index'),

    # --- API Endpoints ---
    path('api/wallet/generate/', views.api_generate_wallet, name='api_generate_wallet'),
    path('api/bnb/transfer/', views.api_send_bnb, name='api_send_bnb'),
    path('api/token/transfer/', views.api_send_token, name='api_send_token'),
]