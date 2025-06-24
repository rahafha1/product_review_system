from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProductViewSet,
    RegisterView,
    LogoutView,
    ReviewListCreateView,
    ReviewDetailView,
    ApproveReviewView,
)

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')

urlpatterns = [
    # Auth URLs
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Reviews URLs
    path('products/<int:product_id>/reviews/', 
         ReviewListCreateView.as_view(), 
         name='review-list'),  
    
    path('products/<int:product_id>/reviews/<int:review_id>/', 
         ReviewDetailView.as_view(), 
         name='review-detail'),  
    
    path('products/<int:product_id>/reviews/<int:review_id>/approve/', 
         ApproveReviewView.as_view(), 
         name='approve-review'), 

    # API Root (ViewSet)
    path('', include(router.urls)),
]