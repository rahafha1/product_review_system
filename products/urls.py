from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, RegisterView, LogoutView, ReviewListCreateView, ReviewDetailView,ApproveReviewView

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')

urlpatterns = [
    # Auth URLs
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Product & Reviews URLs
    path('products/<int:product_id>/reviews/', ReviewListCreateView.as_view(), name='review-list-create'),
    path('products/<int:product_id>/reviews/<int:review_id>/', ReviewListCreateView.as_view(), name='review-detail-by-product'),

    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),
    path('admin/reviews/<int:pk>/approve/', ApproveReviewView.as_view(), name='admin-review-approve'),
    path('', include(router.urls)),
]