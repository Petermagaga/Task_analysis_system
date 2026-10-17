
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from companies.models import WorkItem
from .serializers import WorkItemSerializer


class WorkItemListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = WorkItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        queryset = WorkItem.objects.filter(
            company_id=user.company_id
        )

        if user.role == "EMPLOYEE":
            queryset = queryset.filter(owner=user)

        elif user.role == "SUPERVISOR":
            queryset = queryset.filter(
                department_id=user.department_id
            )

        # Managers and admins can see company work items.
        return (
            queryset
            .select_related("department", "owner")
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        user = self.request.user

        serializer.save(
            company=user.company,
            owner=user,
            department=user.department,
            status=WorkItem.Status.DRAFT,
        )



password="UniquePassword123!"

