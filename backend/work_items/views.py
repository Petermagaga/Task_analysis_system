from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404

from rest_framework import generics,serializers,status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from companies.models import WorkItem
from .serializers import WorkItemSerializer
from .services import transition_work_item

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

password2="ReplaceWithYourOwnStrongTestPassword!"

class WorkItemTransitionAPIView(APIView):
    permission_classes =[IsAuthenticated]

    def post(self,request,work_item_id):
        user=request.user
        #Begin with records belonging to the user's company

        queryset= WorkItem.objects.filter(
            company_id=user.company_id
        )

        #apply the same visibility boundaries as the list

        if user.role=="EMPLOYEE":
            queryset=queryset.filter(owner=user)
        elif user.role== "SUPERVISOR":
            queryset=queryset.filter(
                department_id=user.department_id
            )
        work_item=get_object_or_404(queryset,
                                    id=work_item_id,)

        new_status=request.data.get("status")

        if not isinstance(new_status,str) or not new_status:
            raise serializers.ValidationError({
                "status":"A target status is required."
            })

        try:
            work_item=transition_work_item(work_item,
                                           new_status,)

        except DjangoValidationError as exc:
            detail =(
                exc.message_dict
                if hasattr(exc,'message_dict')
                else exc.messages
            )
            raise serializers.ValidationError(detail) from exc

        return Response({
            "id":str(work_item.id),
            "title":work_item.title,
            "status":work_item.status,
        },
        status=status.HTTP_200_OK,
        )

    