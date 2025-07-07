from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, RegisterView, LogoutView, ReviewListCreateView, ReviewDetailView,ApproveReviewView , ProductRatingInfoView ,ReviewInteractionViewSet , ProductTopReviewView, AdminReportView, AdminReviewActionView, AdminDashboardView ,NotificationListView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from products.views import   ProductAnalyticsView,TopRatedProductsView, TopReviewersView, KeywordSearchView, ExportAllReviewsAnalyticsToCSV,AllProductsAnalyticsView,ExportReviewsToExcel,NotificationListView
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
    path('products/<int:product_id>/reviews/<int:review_id>/', ReviewDetailView.as_view(), name='review-detail-by-product'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),
    path('admin/reviews/<int:pk>/approve/', ApproveReviewView.as_view(), name='admin-review-approve'),
    path('products/<int:pk>/ratings/', ProductRatingInfoView.as_view(), name='product-ratings'),
    path('products/<int:pk>/top-review/', ProductTopReviewView.as_view(), name='product-top-review'),

    # Admin Insights & Reports URLs
    path('admin/reports/', AdminReportView.as_view(), name='admin-reports'),
    path('admin/reviews/<int:review_id>/<str:action>/', AdminReviewActionView.as_view(), name='admin-review-action'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),

    path('notifications/', NotificationListView.as_view(), name='notifications'),
   ####ProductAnalytics
    #AllProductsAnalytics
    path('analytics/all/', AllProductsAnalyticsView.as_view(), name='all_products_analytics'),
     # oneProductAnalytics
    path('analytics/<int:product_id>/', ProductAnalyticsView.as_view(), name='product_analytics'),
    ###TopRatedProduct
    path('analytics/top-rated/', TopRatedProductsView.as_view(), name='top_rated_products'),
    ####top-reviewers
    path('analytics/top-reviewers/', TopReviewersView.as_view(), name='top_reviewers'),
    path('analytics/keyword-search/', KeywordSearchView.as_view(), name='keyword_search'),
    ###export
    path('analytics/export-reviews/', ExportAllReviewsAnalyticsToCSV.as_view(), name='export_reviews_csv'),
    path('analytics/export-reviews-excel/', ExportReviewsToExcel.as_view(), name='export_reviews_csv'),
    path('', include(router.urls)),
]