from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import os
import pandas as pd


class PortfolioAnalysisViewTests(TestCase):
    def setUp(self):
        """Set up test environment."""
        self.client = Client()
        self.url = reverse('portfolio_analysis')  # URL for the file upload form
        self.test_file_path = "test_portfolio.xlsx"
        self.create_sample_excel(self.test_file_path)

    def tearDown(self):
        """Clean up test files."""
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    def create_sample_excel(self, file_path):
        """Create a sample Excel file for testing."""
        details_data = {
            'A': ['Name', 'Phone', 'PAN'],
            'B': ['John Doe', '1234567890', 'ABCDE1234F']
        }
        summary_data = {
            'A': ['Total Investments', 'Current Value', 'Total Profit/Loss', '% Profit/Loss'],
            'B': [100000, 120000, 20000, '20%']
        }
        holdings_data = {
            'Scheme Name': ['Fund A', 'Fund B'],
            'AMC': ['AMC A', 'AMC B'],
            'Category': ['Equity', 'Debt'],
            'Sub-category': ['Large Cap', 'Short Duration'],
            'Folio No.': ['123', '456'],
            'Source': ['Direct', 'Regular'],
            'Units': [100, 200],
            'Invested Value': [50000, 50000],
            'Current Value': [70000, 50000],
            'Returns': [20000, 0],
            'XIRR': ['20%', '5%']
        }
        with pd.ExcelWriter(file_path) as writer:
            pd.DataFrame(details_data).to_excel(writer, index=False, startrow=2)
            pd.DataFrame(summary_data).to_excel(writer, index=False, startrow=12)
            pd.DataFrame(holdings_data).to_excel(writer, index=False, startrow=21)

    def test_get_request(self):
        """Test that the GET request displays the file upload form."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")

    def test_valid_file_upload(self):
        """Test file upload with a valid Excel file."""
        with open(self.test_file_path, "rb") as file:
            uploaded_file = SimpleUploadedFile(
                name="test_portfolio.xlsx",
                content=file.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        response = self.client.post(self.url, {"file": uploaded_file})
        self.assertEqual(response.status_code, 200)

    #     # Validate JSON response
        json_response = response.json()
        self.assertIn("personal_details", json_response)
        self.assertIn("summary", json_response)
        self.assertIn("holdings", json_response)

    #     # Check personal details
        personal_details = json_response["personal_details"]
        self.assertEqual(personal_details["name"], "John Doe")
        self.assertEqual(personal_details["phone"], "1234567890")
        self.assertEqual(personal_details["pan"], "ABCDE1234F")

    #     # Check summary
        summary = json_response["summary"]
        print(summary, '#####')
        self.assertEqual(summary["total_investments"], 100000)
        # self.assertEqual(summary["current_value"], 120000)
    #     self.assertEqual(summary["total_profit_loss"], 20000)
    #     self.assertEqual(summary["profit_loss_percent"], '20%')

    def test_invalid_file_upload(self):
        """Test file upload with an invalid file format."""
        invalid_file = SimpleUploadedFile(
            name="invalid_file.txt",
            content=b"This is not an Excel file.",
            content_type="text/plain"
        )
        response = self.client.post(self.url, {"file": invalid_file})
        self.assertEqual(response.status_code, 400)
        # self.assertContains(response, "Invalid file format")

    def test_empty_form_submission(self):
        """Test form submission without attaching a file."""
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 200)

    def test_excel_processing_error(self):
        """Test if an error in Excel processing is handled gracefully."""
        # Create an Excel file with missing required data
        error_file_path = "error_portfolio.xlsx"
        with pd.ExcelWriter(error_file_path) as writer:
            pd.DataFrame({"A": [], "B": []}).to_excel(writer, index=False)

        with open(error_file_path, "rb") as file:
            uploaded_file = SimpleUploadedFile(
                name="error_portfolio.xlsx",
                content=file.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        response = self.client.post(self.url, {"file": uploaded_file})
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

        if os.path.exists(error_file_path):
            os.remove(error_file_path)
