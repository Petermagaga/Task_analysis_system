from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from companies.models import WorkItem
from .serializers import WorkItemSerializer


class WorkItemListCreateAPIView(generics.ListCreateAPIView):
    serializer_class=WorkItemSerializer
    permission_classes=[IsAuthenticated]

    def get_queryset(self):
        return (
            WorkItem.objects.filter(company_id=self.request.user.company_id)
            .select_related("department","owner")
            .order_by("-created_at")
        )

    def perform_create(self,serializer):
        user=self.request.user
        serializer.save(
            company=user.company,
            owner=user,
            status=WorkItem.Status.DRAFT
        )
