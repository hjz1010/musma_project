
from django.urls import path
# from detection.views import startdetect
from .views import EquipmentTotalView

urlpatterns = [
    path('equipmenttotal', EquipmentTotalView.as_view())
]
