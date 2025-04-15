
from django.urls import path
#from django.contrib.auth.views import LoginView, LogoutView
from .views import (account_view, CheckOutView, ItemDetailView, checkout, HomeView, add_to_cart, remove_from_cart, OrderSummaryView, remove_single_item_from_cart, OrderHistoryView, OrderDetailView, RescheduleOrderView, PromotionsView, complete_profile)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('checkout/', CheckOutView.as_view(), name='checkout-page'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug>/', remove_from_cart, name='remove-from-cart'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('remove-item-from-cart/<slug>/', remove_single_item_from_cart,
         name='remove-single-item-from-cart'),
    path('order-history', OrderHistoryView.as_view(), name='order-history'),
    path('order-detail/<slug>/', OrderDetailView.as_view(), name='order-detail'),
    path('account/', account_view, name='account'),
    path("order/<slug>/reschedule/", RescheduleOrderView.as_view(), name="reschedule-order"),
    path('promotions/', PromotionsView.as_view(), name='promotions'),
    path('complete-profile/', complete_profile, name='complete_profile'),

]