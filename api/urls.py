from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('branches',        views.BranchViewSet,        basename='branch')
router.register('employees',       views.EmployeeViewSet,       basename='employee')
router.register('customers',       views.CustomerViewSet,       basename='customer')
router.register('properties',      views.PropertyViewSet,       basename='property')
router.register('potential-buyers',views.PotentialBuyerViewSet, basename='potentialbuyer')
router.register('buyer-interests', views.BuyerInterestViewSet,  basename='buyerinterest')
router.register('transactions',    views.TransactionViewSet,    basename='transaction')

urlpatterns = [
    path('',          include(router.urls)),
    path('login/',    views.api_login,    name='api_login'),
    path('logout/',   views.api_logout,   name='api_logout'),
    path('me/',       views.api_me,       name='api_me'),
    path('stats/',    views.admin_stats,  name='admin_stats'),
]
