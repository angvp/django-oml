from django.urls import include, path

urlpatterns = [
    path('oml/', include('oml.urls')),
]
