from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views import View
from django import forms
from django.conf import settings
import pandas as pd
import os
import math

from typing import List, Dict, Any


def hello_world(request):
    return HttpResponse("Hello, World!")

# Form for file upload
class FileUploadForm(forms.Form):
    file = forms.FileField()

# Function to save uploaded file
def save_uploaded_file(request) -> str:
    uploaded_file = request.FILES['file']
    file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)
    with open(file_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)
    return file_path

# Function to change the datatypes
def change_type(df: pd.DataFrame, columns: List) -> pd.DataFrame:
    for column in columns:
        df[column] = df[column].astype('float')
    return df

# Function to process the uploaded Excel file
def process_excel_file(file_path: str) -> Dict[Any, Any]:
    data = pd.ExcelFile(file_path)
    sheet_data = data.parse(data.sheet_names[0])

    # Get basic details
    details_start_row = 1
    name = sheet_data.iloc[details_start_row + 1, 1]
    phone = sheet_data.iloc[details_start_row + 2, 1]
    pan = sheet_data.iloc[details_start_row + 3, 1]

    # Extract summary
    summary_start_row = 11
    total_investments = sheet_data.iloc[summary_start_row + 1, 1]
    current_value = sheet_data.iloc[summary_start_row + 1, 2]
    total_profit_loss = sheet_data.iloc[summary_start_row + 1, 3]
    profit_loss_percent = sheet_data.iloc[summary_start_row + 1, 4]

    # Extract holdings
    holdings_start_row = 20
    holdings_data = sheet_data.iloc[holdings_start_row:, :].dropna(how="all")
    holdings_data.columns = [
        "Scheme Name", "AMC", "Category", "Sub-category", "Folio No.", "Source", "Units",
        "Invested Value", "Current Value", "Returns", "XIRR"
    ]

    holdings_data = holdings_data[1:]  # Skip header row
    holdings_data = change_type(df=holdings_data, columns=['Units', 'Invested Value', 'Current Value', 'Returns'])
    holdings_data = holdings_data.fillna(0)

    return {
        "personal_details": {
            "name": name,
            "phone": phone,
            "pan": pan,
        },
        "summary": {
            "total_investments": float(total_investments),
            "current_value": float(current_value),
            "total_profit_loss": total_profit_loss,
            "profit_loss_percent": profit_loss_percent,
        },
        "holdings": holdings_data.to_dict(orient="records")
    }

# Function to delete the uploaded file
def delete_uploaded_file(file_path: str) -> None:
    if os.path.exists(file_path):
        os.remove(file_path)

# View for handling file upload and analysis
class PortfolioAnalysisView(View):
    template_name = "pf_analysis.html"

    def get(self, request):
        form = FileUploadForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = FileUploadForm(request.POST, request.FILES)

        if form.is_valid():
            # Save the file
            file_path = save_uploaded_file(request)

            try:
                # Process the Excel file
                result = process_excel_file(file_path)
            except Exception as e:
                return JsonResponse({"error": str(e)}, status=400)
            finally:
                # Delete the file after processing
                delete_uploaded_file(file_path)

            return JsonResponse(result)

        return render(request, self.template_name, {"form": form, "error": "Invalid file format"})
