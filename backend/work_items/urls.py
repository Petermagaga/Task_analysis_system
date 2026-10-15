from django.urls import path
from .views import WorkItemListCreateAPIView

urlpatterns = [
    path("",WorkItemListCreateAPIView.as_view(),name="work-item-list-create"),
]
