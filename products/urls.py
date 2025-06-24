from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, RegisterView, LogoutView, ReviewListCreateView, ReviewDetailView,ApproveReviewView , ProductRatingInfoView ,ReviewInteractionViewSet , ProductTopReviewView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register(r'review-interactions', ReviewInteractionViewSet, basename='reviewinteraction')

urlpatterns = [
    # Auth URLs
    path('register/', RegisterView.as_view(), name='register'),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # تسجيل دخول
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'), # تجديد توكن
    path('logout/', LogoutView.as_view(), name='logout'),
    # Product & Reviews URLs
    path('products/<int:product_id>/reviews/', ReviewListCreateView.as_view(), name='review-list-create'),
    path('products/<int:product_id>/reviews/<int:review_id>/', ReviewListCreateView.as_view(), name='review-detail-by-product'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),
    path('admin/reviews/<int:pk>/approve/', ApproveReviewView.as_view(), name='admin-review-approve'),
    path('products/<int:pk>/ratings/', ProductRatingInfoView.as_view(), name='product-ratings'),
    path('products/<int:pk>/top-review/', ProductTopReviewView.as_view(), name='product-top-review'),

    path('', include(router.urls)),
]