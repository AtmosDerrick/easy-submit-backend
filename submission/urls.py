from django.urls import path
from .views import SubmissionCreateView, SubmissionConfirmView, SubmissionWithdrawView, SubmissionDetailView, AllUserSubmissionView, LecturerGroupSubmissionsView,LecturerSubmissionDetailView,LecturerReviewView,StudentGroupHistoryView

urlpatterns = [
    path('', SubmissionCreateView.as_view(), name='submission-create'),
    path('<uuid:pk>/check', SubmissionDetailView.as_view(), name='submission-details'),

    path('<uuid:pk>/confirm/', SubmissionConfirmView.as_view(), name='submission-confirm'),
    path('<uuid:pk>/withdraw/', SubmissionWithdrawView.as_view(), name='submission-withdraw'),
    
    path('my-submissions/', AllUserSubmissionView.as_view(), name='my-submissions'),
    
     # ── Lecturer ──────────────────────────────────────────────────────────
    # Lecturer clicks a group → sees all submissions in that group
    path('group/<uuid:course_id>/',   LecturerGroupSubmissionsView.as_view(), name='lecturer-group-submissions'),
    path('<uuid:pk>/detail/',       LecturerSubmissionDetailView.as_view(),name='lecturer-submission-detail'),
     path('<uuid:pk>/review/',       LecturerReviewView.as_view(),            name='lecturer-review'),
     path('history/<uuid:course_id>/', StudentGroupHistoryView.as_view(), name='student-group-history'),


]
 

