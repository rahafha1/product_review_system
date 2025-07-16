from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, RegisterView, LogoutView, ReviewListCreateView, ReviewDetailView, ApproveReviewView, ProductRatingInfoView, ReviewInteractionViewSet, ProductTopReviewView, AdminReportView, AdminReviewActionView, AdminDashboardView, NotificationListView, ReviewCommentViewSet, AddCommentToReview
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from products.views import ProductAnalyticsView, TopRatedProductsView, TopReviewersView, KeywordSearchView, ExportAllReviewsAnalyticsToCSV, AllProductsAnalyticsView, ExportReviewsToExcel, NotificationListView
from django.urls import re_path

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register(r'review-interactions', ReviewInteractionViewSet, basename='review-interaction')
router.register(r'review-comments', ReviewCommentViewSet, basename='reviewcomment')

# رابط مخصص للإحصائيات
review_interaction_stats = ReviewInteractionViewSet.as_view({'get': 'review_interaction_stats'})

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('products/<int:product_id>/reviews/', ReviewListCreateView.as_view(), name='review-list-create'),
    path('products/<int:product_id>/reviews/<int:review_id>/', ReviewDetailView.as_view(), name='review-detail-by-product'),
    path('reviews/<int:review_id>/', ReviewDetailView.as_view(), name='review-detail'),
    path('reviews/<int:review_id>/comment/', AddCommentToReview.as_view(), name='add-review-comment'),
    path('admin/review/approve/<int:product_id>/<int:review_id>/', ApproveReviewView.as_view(), name='admin-review-approve'),
    path('products/<int:pk>/ratings/', ProductRatingInfoView.as_view(), name='product-ratings'),
    path('products/<int:pk>/top-review/', ProductTopReviewView.as_view(), name='product-top-review'),
    path('admin/reports/', AdminReportView.as_view(), name='admin-reports'),
    path('admin/reviews/<int:review_id>/<str:action>/', AdminReviewActionView.as_view(), name='admin-review-action'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('notifications/', NotificationListView.as_view(), name='notifications'),
    path('analytics/all/', AllProductsAnalyticsView.as_view(), name='all_products_analytics'),
    path('analytics/<int:product_id>/', ProductAnalyticsView.as_view(), name='product_analytics'),
    path('analytics/top-rated/', TopRatedProductsView.as_view(), name='top_rated_products'),
    path('analytics/top-reviewers/', TopReviewersView.as_view(), name='top_reviewers'),
    path('analytics/keyword-search/', KeywordSearchView.as_view(), name='keyword_search'),
    path('analytics/export-reviews/', ExportAllReviewsAnalyticsToCSV.as_view(), name='export_reviews_csv'),
    path('analytics/export-reviews-excel/', ExportReviewsToExcel.as_view(), name='export_reviews_excel'),

    # ✅ الرابط المضاف للإحصائيات
    path('review-interactions/<int:review_id>/stats/', review_interaction_stats, name='review-interaction-stats'),

    path('', include(router.urls)),
]
