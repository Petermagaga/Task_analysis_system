from django.db import IntegrityError
from django.test import TestCase

from companies.models import Company, Department


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