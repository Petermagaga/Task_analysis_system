from django.urls import path

from .views import (
    WorkItemListCreateAPIView,
    WorkItemTransitionAPIView,
    WorkExecutionStartAPIView,
    WorkExecutionStopAPIView,
)

urlpatterns = [
    path(
        "",
        WorkItemListCreateAPIView.as_view(),
        name="work-item-list-create",
    ),
    path(
        "<uuid:work_item_id>/transition/",
        WorkItemTransitionAPIView.as_view(),
        name="work-item-transition",
    ),
    path(
        "<uuid:work_item_id>/executions/start/",
        WorkExecutionStartAPIView.as_view(),
        name="work-execution-start",
    ),
    path(
        "executions/<uuid:execution_id>/stop/",
        WorkExecutionStopAPIView.as_view(),
        name="work-execution-stop",
    ),
]