from django.urls import path
from .views import SubmissionCreateView, SubmissionConfirmView, SubmissionWithdrawView, SubmissionDetailView

urlpatterns = [
    path('', SubmissionCreateView.as_view(), name='submission-create'),
    path('<uuid:pk>', SubmissionDetailView.as_view(), name='submission-details'),

    path('<uuid:pk>/confirm/', SubmissionConfirmView.as_view(), name='submission-confirm'),
    path('<uuid:pk>/withdraw/', SubmissionWithdrawView.as_view(), name='submission-withdraw'),
]