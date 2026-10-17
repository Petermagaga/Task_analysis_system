
from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import User
from companies.models import Company, Department, WorkItem


class WorkItemAPITests(APITestCase):
    def setUp(self):
        # Create the first company and its department.
        self.company = Company.objects.create(
            name="API Test Company",
            code="APITEST",
        )

        self.department = Department.objects.create(
            company=self.company,
            name="Production",
            code="APIPROD",
        )

        # Create a second department for permission tests.
        self.other_department = Department.objects.create(
            company=self.company,
            name="Finance",
            code="APIFIN",
        )

        # Create the first employee.
        self.employee = User.objects.create_user(
            username="api_employee_one",
            email="api_employee_one@example.com",
            password="Test-Only-Password-123!",
            company=self.company,
            department=self.department,
            role="EMPLOYEE",
        )

        # Create another employee in the same department.
        self.other_employee = User.objects.create_user(
            username="api_employee_two",
            email="api_employee_two@example.com",
            password="Another-Test-Password-456!",
            company=self.company,
            department=self.department,
            role="EMPLOYEE",
        )

        # Authenticate using JWT access tokens.
        self.client.credentials(
            HTTP_AUTHORIZATION=(
                f"Bearer {self.get_access_token(self.employee)}"
            )
        )

        self.url = "/api/work-items/"

    @staticmethod
    def get_access_token(user):
        return str(RefreshToken.for_user(user).access_token)

    def valid_payload(self, **overrides):
        payload = {
            "department": str(self.department.id),
            "title": "Repair stitching machine",
            "description": "Inspect and repair the stitching machine.",
            "work_type": "TASK",
            "planned_at": (
                timezone.now() + timedelta(days=1)
            ).isoformat(),
        }
        payload.update(overrides)
        return payload

    def test_unauthenticated_user_cannot_list_work_items(self):
        self.client.credentials()

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_employee_can_create_work_item(self):
        response = self.client.post(
            self.url,
            self.valid_payload(),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )

        item = WorkItem.objects.get(
            title="Repair stitching machine"
        )

        self.assertEqual(item.company_id, self.company.id)
        self.assertEqual(item.department_id, self.department.id)
        self.assertEqual(item.owner_id, self.employee.id)
        self.assertEqual(item.status, WorkItem.Status.DRAFT)

    def test_employee_cannot_see_another_employees_work_item(self):
        WorkItem.objects.create(
            company=self.company,
            department=self.department,
            owner=self.other_employee,
            title="Other employee task",
            work_type="TASK",
            planned_at=timezone.now() + timedelta(days=1),
        )

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK,)
        self.assertEqual(response.data, [])

    def test_employee_cannot_create_work_for_another_department(self):
        response = self.client.post(
            self.url,
            self.valid_payload(
                department=str(self.other_department.id)
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.assertFalse(
            WorkItem.objects.filter(
                title="Repair stitching machine"
            ).exists()
        )

    def test_owner_cannot_be_changed_by_submitting_another_user_id(self):
        payload = self.valid_payload()
        payload["owner"] = str(self.other_employee.id)

        response = self.client.post(
            self.url,
            payload,
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            response.data,
        )

        item = WorkItem.objects.get(
            title="Repair stitching machine"
        )

        self.assertEqual(item.owner_id, self.employee.id)
        self.assertNotEqual(item.owner_id, self.other_employee.id)

    def test_due_date_cannot_be_before_planned_time(self):
        planned_at = timezone.now() + timedelta(days=2)
        due_at = planned_at - timedelta(hours=1)

        response = self.client.post(
            self.url,
            self.valid_payload(
                planned_at=planned_at.isoformat(),
                due_at=due_at.isoformat(),
            ),
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertIn("due_at", response.data)
