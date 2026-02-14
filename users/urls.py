from django.urls import path
from . import views

urlpatterns = [
    # Current user
    path('me/', views.UserDetailView.as_view(), name='user-detail'),
    path('me/update/', views.UpdateProfileView.as_view(), name='update-profile'),
    path('me/delete/', views.DeleteAccountView.as_view(), name='delete-account'),
    
    # Public users
    path('list/', views.UserListView.as_view(), name='user-list'),
    path('search/', views.SearchUsersView.as_view(), name='search-users'),
    path('username/<str:username>/', views.GetUserByUsernameView.as_view(), name='user-by-username'),
    path('<str:id>/', views.GetUserByIdView.as_view(), name='user-by-username'),

    path('', views.health_check, name='health-check'),
]