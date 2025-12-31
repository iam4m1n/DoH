from django.urls import path
from . import views

urlpatterns = [
    # API endpoints
    path('dns-query', views.doh_query),
    path('admin/record', views.add_record),
    path('admin/records', views.list_records),
    path('admin/record/<str:domain>', views.delete_record),
    
    # Web UI endpoints
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('query/', views.query_dns, name='query_dns'),
    path('records/', views.records_list, name='records_list'),
    path('records/add/', views.add_record_view, name='add_record_view'),
    path('records/<int:record_id>/edit/', views.edit_record_view, name='edit_record'),
    path('records/<int:record_id>/delete/', views.delete_record_view, name='delete_record'),
]
