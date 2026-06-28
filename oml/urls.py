from django.urls import path

from . import views

app_name = 'oml'

urlpatterns = [
    path('moderation/', views.moderation_panel, name='moderation_panel'),
    path('approve/<int:object_id>/<int:ctype_id>/', views.approve, name='approve_object'),
    path('reject/<int:object_id>/<int:ctype_id>/', views.reject_view, name='reject_object'),
    path('approve/bulk/', views.approve_bulk, name='approve_bulk'),
]
