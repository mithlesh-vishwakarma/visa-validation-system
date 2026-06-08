from django.test import TestCase
from services.ocr_service import parse_text_data
from services.rules_service import run_submission_validation
from authentication.models import Organization, User
from clients.models import Client
from submissions.models import Submission, Document, ValidationReport
from rules_engine.models import CountryRule
from datetime import datetime, timedelta

class OCRServiceTest(TestCase):
    def test_passport_parsing(self):
        passport_text = """
        PASSPORT - CANADA
        Name: John Doe
        Passport Number: Z9876543
        Date of Expiry: 2032-12-31
        Date of Birth: 1990-05-15
        """
        data = parse_text_data(passport_text, 'Passport')
        self.assertEqual(data.get('passport_number'), 'Z9876543')
        self.assertEqual(data.get('name'), 'John Doe')
        self.assertEqual(data.get('expiry_date'), '2032-12-31')

    def test_bank_statement_parsing(self):
        bank_text = """
        Royal Bank of Canada
        Account Name: John Doe
        Closing Balance: 350000.00
        Available Balance: 350000.00
        """
        data = parse_text_data(bank_text, 'Bank Statement')
        self.assertEqual(data.get('bank_balance'), 350000.0)
        self.assertEqual(data.get('name'), 'John Doe')


class RulesEngineTest(TestCase):
    def setUp(self):
        # Create Organization
        self.org = Organization.objects.create(name="Test Consulting Agency")
        
        # Create User
        self.user = User.objects.create_user(
            email="agent@test.com",
            password="testpassword",
            first_name="Agent",
            last_name="One",
            organization=self.org
        )

        # Create Client
        self.client = Client.objects.create(
            organization=self.org,
            name="Rahul Sharma",
            passport_number="P1234567",
            country="Canada",
            visa_type="Tourist",
            mobile="+919876543210",
            email="rahul@sharma.com"
        )

        # Create Country Rule
        self.rule = CountryRule.objects.create(
            country="Canada",
            visa_type="Tourist",
            required_documents=["Passport", "Bank Statement"],
            rules={"passport_min_validity_months": 6, "min_bank_balance": 300000}
        )

    def test_rules_validation_pass(self):
        # Create Submission
        submission = Submission.objects.create(
            client=self.client,
            country="Canada",
            visa_type="Tourist",
            created_by=self.user,
            status="Pending"
        )

        # Valid documents
        passport_expiry = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        doc_passport = Document.objects.create(
            submission=submission,
            name="Passport",
            file_url="/media/uploads/mock_passport.pdf",
            status="Pending",
            extracted_data={
                "passport_number": "P1234567",
                "name": "Rahul Sharma",
                "expiry_date": passport_expiry
            }
        )
        
        doc_bank = Document.objects.create(
            submission=submission,
            name="Bank Statement",
            file_url="/media/uploads/mock_bank.pdf",
            status="Pending",
            extracted_data={
                "bank_balance": 350000.0,
                "name": "Rahul Sharma"
            }
        )

        # Run validation
        report = run_submission_validation(submission.id)
        
        self.assertIsNotNone(report)
        self.assertEqual(report.score, 100)
        self.assertEqual(report.status, 'Passed')
        
        submission.refresh_from_db()
        self.assertEqual(submission.status, 'Under Review')
        
        # Verify document updates
        doc_passport.refresh_from_db()
        doc_bank.refresh_from_db()
        self.assertEqual(doc_passport.status, 'Valid')
        self.assertEqual(doc_bank.status, 'Valid')

    def test_rules_validation_fail_low_balance(self):
        submission = Submission.objects.create(
            client=self.client,
            country="Canada",
            visa_type="Tourist",
            created_by=self.user,
            status="Pending"
        )

        passport_expiry = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        Document.objects.create(
            submission=submission,
            name="Passport",
            file_url="/media/uploads/mock_passport.pdf",
            status="Pending",
            extracted_data={
                "passport_number": "P1234567",
                "name": "Rahul Sharma",
                "expiry_date": passport_expiry
            }
        )
        
        # Low balance (150k instead of 300k minimum requirement)
        Document.objects.create(
            submission=submission,
            name="Bank Statement",
            file_url="/media/uploads/mock_bank.pdf",
            status="Pending",
            extracted_data={
                "bank_balance": 150000.0,
                "name": "Rahul Sharma"
            }
        )

        report = run_submission_validation(submission.id)
        
        self.assertIsNotNone(report)
        self.assertEqual(report.score, 70) # 100 - 30 for low balance
        self.assertEqual(report.status, 'Warning') # Passport is valid and no missing docs
        self.assertIn("below the minimum requirement", report.issues[0])
