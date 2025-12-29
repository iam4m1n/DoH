from django.urls import path
from . import views

urlpatterns = [
    path('dns-query', views.doh_query),
    path('admin/record', views.add_record),
    path('admin/records', views.list_records),
    path('admin/record/<str:domain>', views.delete_record),
]
