from django.db import IntegrityError
from django.test import TestCase
from django.core.exceptions import ValidationError
from companies.models import Company, Department,WorkSchedule,WorkItem
from accounts.models import User

class CompanyModelTests(TestCase):

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST",
            timezone="Africa/Nairobi",
        )

    def test_company_is_created_with_uuid(self):
        self.assertIsNotNone(self.company.id)

    def test_company_is_active_by_default(self):
        self.assertTrue(self.company.is_active)

    def test_company_string_representation(self):
        self.assertEqual(
            str(self.company),
            "Test Company (TEST)",
        )


class DepartmentModelTests(TestCase):

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST",
        )

    def test_department_belongs_to_company(self):
        department = Department.objects.create(
            company=self.company,
            name="Finance",
            code="FIN",
        )

        self.assertEqual(
            department.company,
            self.company,
        )

    def test_department_code_must_be_unique_within_company(self):
        Department.objects.create(
            company=self.company,
            name="Finance",
            code="FIN",
        )

        with self.assertRaises(IntegrityError):
            Department.objects.create(
                company=self.company,
                name="Another Finance",
                code="FIN",
            )

    def test_same_department_code_allowed_for_different_companies(self):
        another_company = Company.objects.create(
            name="Another Company",
            code="ANOTHER",
        )

        Department.objects.create(
            company=self.company,
            name="Finance",
            code="FIN",
        )

        department = Department.objects.create(
            company=another_company,
            name="Finance",
            code="FIN",
        )

        self.assertEqual(department.code, "FIN")

class WorkScheduleModelTests(TestCase):

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST",
        )

    def test_valid_work_schedule(self):
        schedule = WorkSchedule(
            company=self.company,
            name="Standard Hours",
            timezone="Africa/Nairobi",
            start_time="08:00",
            end_time="17:00",
            break_start="13:00",
            break_end="14:00",
            working_days=[0, 1, 2, 3, 4],
        )

        schedule.full_clean()

    def test_end_time_must_be_after_start_time(self):
        schedule = WorkSchedule(
            company=self.company,
            name="Invalid Hours",
            timezone="Africa/Nairobi",
            start_time="17:00",
            end_time="08:00",
            working_days=[0, 1, 2, 3, 4],
        )

        with self.assertRaises(ValidationError):
            schedule.full_clean()

    def test_break_must_be_inside_working_hours(self):
        schedule = WorkSchedule(
            company=self.company,
            name="Invalid Break",
            timezone="Africa/Nairobi",
            start_time="08:00",
            end_time="17:00",
            break_start="07:00",
            break_end="14:00",
            working_days=[0, 1, 2, 3, 4],
        )

        with self.assertRaises(ValidationError):
            schedule.full_clean()

    def test_break_start_and_end_must_be_provided_together(self):
        schedule = WorkSchedule(
            company=self.company,
            name="Incomplete Break",
            timezone="Africa/Nairobi",
            start_time="08:00",
            end_time="17:00",
            break_start="13:00",
            working_days=[0, 1, 2, 3, 4],
        )

        with self.assertRaises(ValidationError):
            schedule.full_clean()

    def test_working_days_cannot_be_empty(self):
        schedule = WorkSchedule(
            company=self.company,
            name="No Working Days",
            timezone="Africa/Nairobi",
            start_time="08:00",
            end_time="17:00",
            working_days=[],
        )

        with self.assertRaises(ValidationError):
            schedule.full_clean()

    def test_working_days_must_be_between_zero_and_six(self):
        schedule = WorkSchedule(
            company=self.company,
            name="Invalid Days",
            timezone="Africa/Nairobi",
            start_time="08:00",
            end_time="17:00",
            working_days=[0, 1, 7],
        )

        with self.assertRaises(ValidationError):
            schedule.full_clean()

class WorkItemModelTests(TestCase):

    def setUp(self):
        self.company = Company.objects.create(
            name="Test Company",
            code="TEST",
        )

        self.department = Department.objects.create(
            company=self.company,
            name="Production",
            code="PROD",
        )

        self.user = User.objects.create_user(
            username="employee",
            email="employee@test.com",
            password="TestPassword123!",
            company=self.company,
            department=self.department,
            role=User.Role.EMPLOYEE,
            first_name="Test",
            last_name="Employee",
        )

    def test_work_item_has_uuid(self):
        work_item = WorkItem.objects.create(
            company=self.company,
            department=self.department,
            owner=self.user,
            title="Repair stitching machine",
            planned_at="2026-10-04 08:00:00",
        )

        self.assertIsNotNone(work_item.id)

    def test_work_item_defaults_to_draft(self):
        work_item = WorkItem.objects.create(
            company=self.company,
            department=self.department,
            owner=self.user,
            title="Repair stitching machine",
            planned_at="2026-10-04 08:00:00",
        )

        self.assertEqual(
            work_item.status,
            WorkItem.Status.DRAFT,
        )

    def test_work_item_defaults_to_task(self):
        work_item = WorkItem.objects.create(
            company=self.company,
            department=self.department,
            owner=self.user,
            title="Repair stitching machine",
            planned_at="2026-10-04 08:00:00",
        )

        self.assertEqual(
            work_item.work_type,
            WorkItem.WorkType.TASK,
        )

    def test_work_item_belongs_to_company(self):
        work_item = WorkItem.objects.create(
            company=self.company,
            department=self.department,
            owner=self.user,
            title="Repair stitching machine",
            planned_at="2026-10-04 08:00:00",
        )

        self.assertEqual(
            work_item.company,
            self.company,
        )

    def test_work_item_belongs_to_department(self):
        work_item = WorkItem.objects.create(
            company=self.company,
            department=self.department,
            owner=self.user,
            title="Repair stitching machine",
            planned_at="2026-10-04 08:00:00",
        )

        self.assertEqual(
            work_item.department,
            self.department,
        )

    def test_work_item_has_owner(self):
        work_item = WorkItem.objects.create(
            company=self.company,
            department=self.department,
            owner=self.user,
            title="Repair stitching machine",
            planned_at="2026-10-04 08:00:00",
        )

        self.assertEqual(
            work_item.owner,
            self.user,
        )

    def test_work_item_string_representation(self):
        work_item = WorkItem.objects.create(
            company=self.company,
            department=self.department,
            owner=self.user,
            title="Repair stitching machine",
            planned_at="2026-10-04 08:00:00",
        )

        self.assertEqual(
            str(work_item),
            "Repair stitching machine",
        )

    def test_due_date_cannot_be_before_planned_date(self):
        work_item = WorkItem(
            company=self.company,
            department=self.department,
            owner=self.user,
            title="Repair stitching machine",
            planned_at="2026-10-04 10:00:00",
            due_at="2026-10-04 09:00:00",
        )

        with self.assertRaises(ValidationError):
            work_item.full_clean()

    def test_owner_must_belong_to_same_company(self):
        other_company = Company.objects.create(
            name="Other Company",
            code="OTHER",
        )

        other_department = Department.objects.create(
            company=other_company,
            name="Operations",
            code="OPS",
        )

        other_user = User.objects.create_user(
            username="other_employee",
            email="other@test.com",
            password="TestPassword123!",
            company=other_company,
            department=other_department,
            role=User.Role.EMPLOYEE,
        )

        work_item = WorkItem(
            company=self.company,
            department=self.department,
            owner=other_user,
            title="Invalid company ownership",
            planned_at="2026-10-04 08:00:00",
        )

        with self.assertRaises(ValidationError):
            work_item.full_clean()

    def test_department_must_belong_to_same_company(self):
        other_company = Company.objects.create(
            name="Other Company",
            code="OTHER",
        )

        other_department = Department.objects.create(
            company=other_company,
            name="Operations",
            code="OPS",
        )

        work_item = WorkItem(
            company=self.company,
            department=other_department,
            owner=self.user,
            title="Invalid department",
            planned_at="2026-10-04 08:00:00",
        )

        with self.assertRaises(ValidationError):
            work_item.full_clean()

    def test_owner_department_must_match_work_item_department(self):
        finance = Department.objects.create(
            company=self.company,
            name="Finance",
            code="FIN",
        )

        finance_user = User.objects.create_user(
            username="finance_employee",
            email="finance@test.com",
            password="TestPassword123!",
            company=self.company,
            department=finance,
            role=User.Role.EMPLOYEE,
        )

        work_item = WorkItem(
            company=self.company,
            department=self.department,  # Production
            owner=finance_user,           # Finance
            title="Invalid department ownership",
            planned_at="2026-10-04 08:00:00",
        )

        with self.assertRaises(ValidationError):
            work_item.full_clean()