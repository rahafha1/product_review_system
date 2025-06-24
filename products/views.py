from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .models import Product, Review
from .serializers import ProductSerializer, ReviewSerializer, UserSerializer ,ReviewInteraction , ReviewInteractionSerializer
from .permissions import IsOwnerOrReadOnly, IsProductOwner
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import PermissionDenied, NotFound
from django.db.models import Count, Q , F
## F to bring from database not python mem
# =============================
#  Register View
# =============================
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        if not all([username, email, password]):
            return Response({'error': 'All fields are required'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        refresh = RefreshToken.for_user(user)
        serializer = UserSerializer(user)

        return Response({
            'message': 'User created successfully',
            'user': serializer.data,
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }, status=status.HTTP_201_CREATED)


# =============================
# Logout View
# =============================
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)

        except Exception:
            return Response({"error": "Invalid Token"}, status=status.HTTP_400_BAD_REQUEST)


# =============================
#  Product ViewSet
# =============================
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrReadOnly]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return [perm() for perm in permission_classes]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# =============================
#  Product Rating Info View
# =============================
class ProductRatingInfoView(APIView):
    def get(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

        visible_reviews = product.reviews.filter(is_visible=True)
        avg_rating = round(sum(r.rating for r in visible_reviews) / visible_reviews.count(), 1) if visible_reviews.exists() else 0

        return Response({
            'product': product.name,
            'average_rating': avg_rating,
            'approved_reviews': visible_reviews.count()
        }, status=status.HTTP_200_OK)


# =============================
#  Review List/Create View
# =============================
class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['rating']
    search_fields = ['review_text']
    ordering_fields = ['created_at']

    def get_queryset(self):
        product_id = self.kwargs['product_id']
        queryset = Review.objects.filter(product_id=product_id, is_visible=True)
        rating = self.request.query_params.get('rating')
        if rating:
            queryset = queryset.filter(rating=rating)
        return queryset

    def perform_create(self, serializer):
        product_id = self.kwargs['product_id']
        product = Product.objects.get(id=product_id)
        serializer.save(user=self.request.user, product=product)

    def patch(self, request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        review_id = kwargs.get('review_id')
        try:
            review = Review.objects.get(id=review_id, product_id=product_id)
        except Review.DoesNotExist:
            raise NotFound("Review not found for this product.")
        if review.user != request.user:
            raise PermissionDenied("You do not have permission to edit this review.")
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        product_id = kwargs.get('product_id')
        review_id = kwargs.get('review_id')
        try:
            review = Review.objects.get(id=review_id, product_id=product_id)
        except Review.DoesNotExist:
            raise NotFound("Review not found for this product.")
        if review.user != request.user:
            raise PermissionDenied("You do not have permission to delete this review.")
        review.delete()
        return Response({"message": "Review deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# =============================
# 📄 Review Detail View
# =============================
class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsOwnerOrReadOnly]


# =============================
# ✅ Approve Review (Admin only)
# =============================
class ApproveReviewView(APIView):
    permission_classes = [IsAuthenticated, IsProductOwner]

    def post(self, request, pk=None):
        try:
            review = Review.objects.get(pk=pk)
        except Review.DoesNotExist:
            return Response({'error': 'Review not found'}, status=status.HTTP_404_NOT_FOUND)

        if review.product.user != request.user:
            return Response({'error': 'You are not the owner of this product.'}, status=status.HTTP_403_FORBIDDEN)

        review.is_visible = True
        review.save()
        return Response({'status': 'Review approved!'})

#  New Placeholder Endpoints for Task 8

class AnalyticsView(APIView):
    """For Partner 1: Will implement analytics for reviews"""
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, *args, **kwargs):
        # TODO: Implement analytics
        return Response({"message": "Analytics placeholder"})


### by rahaf ###
class ReviewInteractionViewSet(viewsets.ModelViewSet):
    queryset = ReviewInteraction.objects.all()
    serializer_class = ReviewInteractionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # يسمح للمستخدم فقط برؤية تفاعلاته أو تفاعلات مراجعة معينة
        user = self.request.user
        return ReviewInteraction.objects.filter(user=user)

    def perform_create(self, serializer):
        # ربط التفاعل بالمستخدم الحالي
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='review/(?P<review_id>[^/.]+)/stats')
    def review_stats(self, request, review_id=None):
        # إحصائيات التفاعل على مراجعة معينة
        likes = ReviewInteraction.objects.filter(review_id=review_id, liked=True).count()
        helpfuls = ReviewInteraction.objects.filter(review_id=review_id, is_helpful=True).count()
        return Response({
            "review_id": review_id,
            "likes_count": likes,
            "helpful_count": helpfuls,
        }, status=status.HTTP_200_OK)

class ProductTopReviewView(APIView):
    def get(self, request, pk):
        # تأكد المنتج موجود
        try:
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"detail": "المنتج غير موجود."}, status=status.HTTP_404_NOT_FOUND)

        # جلب مراجعات المنتج مع حساب عدد الإعجابات وعدد التقييمات كمفيد
        reviews = Review.objects.filter(product=product).annotate(
            likes_count=Count('interactions', filter=Q(interactions__liked=True)),
            helpful_count=Count('interactions', filter=Q(interactions__is_helpful=True))
        )

        # ترتيب المراجعات حسب مجموع التفاعلات (الإعجابات + المفيد) نزولاً
        reviews = reviews.annotate(total_interactions=F('likes_count') + F('helpful_count')).order_by('-total_interactions')

        if not reviews.exists():
            return Response({"detail": "لا توجد مراجعات لهذا المنتج."}, status=status.HTTP_404_NOT_FOUND)

        top_review = reviews.first()
        serializer = ReviewSerializer(top_review)
        return Response(serializer.data)

        #### rrr ###
class NotificationListView(APIView):
    """For Partner 3: Will implement user notifications"""
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, *args, **kwargs):
        # TODO: List notifications
        return Response({"message": "Notifications placeholder"})


class AdminReportView(APIView):
    """For Partner 4: Will implement admin reporting"""
    permission_classes = [permissions.IsAdminUser]
    def get(self, request, *args, **kwargs):
        # TODO: Admin reporting (unapproved reviews, low ratings, offensive words)
        return Response({"message": "Admin Reports placeholder"})
