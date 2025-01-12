# from django.contrib import admin
# from django.urls import path
# from . import views
# from .views import  stockingListView, modifyDrugUpdateView

# urlpatterns = [
#     path('', views.home, name='home'),
#     # path('', DrugListView.as_view(), name='home'),
#     path('create/', views.createDrug, name='create'),
#     path('addstock/<int:pk>/', views.addStock, name='addstock'),
#     path('stocking/', stockingListView.as_view(), name='stocking'),
#     path('modify/<int:pk>/', modifyDrugUpdateView.as_view(), name='modify'),
#     path('stocked/', views.StockAdded, name='stocked'),
#     path('sell/<int:pk>/', views.sellDrug, name='sell'),
#     path('search/', views.search, name='search'),
#     path('bin-report/search/', views.binsearch, name='bin_search'),
#     path('search/stock/', views.searchstock, name='searchstock'),
#     path('history/', views.salehistory, name='history'),
#     path('today/', views.todaysales, name='today'),
#     path('bin-report/', views.bin_report, name='bin_report'),
#     path('dashboard/', views.dashboard, name='dashboard'),
#     path('low-stock/', views.low_stock_view, name='low_stock'),


# ]

from django.contrib import admin
from django.urls import path
from . import views
from .views import stockingListView, modifyDrugUpdateView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # Redirect to dashboard by default after login
    path('create/', views.createDrug, name='create'),
    path('addstock/<int:pk>/', views.addStock, name='addstock'),
    path('stocking/', stockingListView.as_view(), name='stocking'),
    path('modify/<int:pk>/', modifyDrugUpdateView.as_view(), name='modify'),
    path('stocked/', views.StockAdded, name='stocked'),
    path('sell/<int:pk>/', views.sellDrug, name='sell'),
    path('lock/<int:pk>/', views.lockDrug, name='lock_item'),
    path('search/', views.search, name='search'),
    path('bin-report/search/', views.binsearch, name='bin_search'),
    path('search/stock/', views.searchstock, name='searchstock'),
    path('history/', views.salehistory, name='history'),
    path('today/', views.todaysales, name='today'),
    path('bin-report/', views.bin_report, name='bin_report'),
    path('out-of-stock/', views.out_of_stock, name='out_of_stock'),
    path('expiring-soon/', views.expiring_soon, name='expiring_soon'),
    path('vaccines/', views.home, name='home'),
    path('low-stock/', views.low_stock_view, name='low_stock'),
    path('get_online_offline_users/', views.get_online_offline_users, name='get_online_offline_users'),
    path('locked-products/', views.locked_products, name='locked_products'),
    path('locked-products/search/', views.locked_search, name='locked_search'),
    path('locked-products/post/<int:lock_id>/', views.post_locked_product, name='post_locked_product'),
    path('locked-products/unlock/<int:lock_id>/', views.unlock_product, name='unlock_product'),
    path('add_user/', views.add_user, name='add_user'),  # URL for adding a user
    path('user_management/', views.user_management, name='user_management'),  # URL for the user management page

]

