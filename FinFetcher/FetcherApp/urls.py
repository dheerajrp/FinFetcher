from django.urls import path
from .views import hello_world, PortfolioAnalysisView

urlpatterns = [
    path('', hello_world, name='hello_world'),
    path('port-folio/', PortfolioAnalysisView.as_view(), name='portfolio_analysis'),
]
