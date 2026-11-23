from django.urls import path

from .views import (
    WorkItemListCreateAPIView,
    WorkItemTransitionAPIView,
    WorkExecutionStartAPIView,
    WorkExecutionStopAPIView,
    WorkItemOutcomeCreateAPIView,
    OutcomeConfirmAPIView,
    OutcomeExecutionAssociationAPIView
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
    path(
        "<uuid:work_item_id>/outcomes/",
        WorkItemOutcomeCreateAPIView.as_view(),
        name="work-item-outcome-create",
    ),
    path(
        "outcomes/<uuid:outcome_id>/confirm/",
        OutcomeConfirmAPIView.as_view(),
        name="work-item-outcome-confirm",
    ),
    path(
        "outcomes/<uuid:outcome_id>/executions/",
        OutcomeExecutionAssociationAPIView.as_view(),
        name="outcome-execution-association",
    ),
]