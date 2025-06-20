from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ReviewViewSet, RegisterView, LogoutView, ReviewListCreateView, ReviewDetailView, ProductRatingInfoView# AdminReviewApprovalView

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('reviews', ReviewViewSet, basename='review')

urlpatterns = [
    # Auth URLs
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Product & Review URLs
    path('products/<int:product_id>/reviews/', ReviewListCreateView.as_view(), name='review-list-create'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),
    path('products/<int:pk>/ratings/', ProductRatingInfoView.as_view(), name='product-rating-info'),
    #path('admin/reviews/<int:pk>/approve/', AdminReviewApprovalView.as_view(), name='admin-review-approve'),
    
    # API Router
    path('', include(router.urls)),
]