from django.urls import path
from .views import (WorkItemListCreateAPIView,WorkItemTransitionAPIView)
urlpatterns = [
    path("",WorkItemListCreateAPIView.as_view(),name="work-item-list-create"),
    path("<uuid:work_item_id>/transition/",WorkItemTransitionAPIView.as_view(),name="work-item-transition",),
]

