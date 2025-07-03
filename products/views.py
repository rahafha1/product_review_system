from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .models import Product, Review, Notification, AdminReport
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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response({
                'success': True,
                'message': 'Review created successfully.',
                'review': serializer.data
            }, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response({
                'success': False,
                'message': 'Failed to create review.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

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

#============================
#  Review Detail View
# =============================
class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsOwnerOrReadOnly]
    lookup_url_kwarg = 'review_id'
# =============================
# ✅ Approve Review (Admin only)
# =============================

class ApproveReviewView(APIView):
    permission_classes = [IsAuthenticated, IsProductOwner]

    def post(self, request, product_id, review_id):
        try:
            # التأكد من أن المراجعة موجودة ومرتبطة بالمنتج المطلوب
            review = Review.objects.get(id=review_id, product_id=product_id)
        except Review.DoesNotExist:
            return Response(
                {'error': 'Review not found for this product.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if review.product.user != request.user:
            return Response(
                {'error': 'You are not the owner of this product.'},
                status=status.HTTP_403_FORBIDDEN
            )

        review.is_visible = True
        review.save()


        return Response({
            'status': 'Review approved!',
            'product_id': product_id,
            'review_id': review_id,
            'product_name': review.product.name
        })

#  New Placeholder Endpoints for Task 8

# class AnalyticsView(APIView):
#     """For Partner 1: Will implement analytics for reviews"""
#     permission_classes = [permissions.IsAuthenticated]
#     def get(self, request, *args, **kwargs):
#         # TODO: Implement analytics
#         return Response({"message": "Analytics placeholder"})


### by rahaf ###
class ReviewInteractionViewSet(viewsets.ModelViewSet):
    queryset = ReviewInteraction.objects.all()
    serializer_class = ReviewInteractionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self.queryset):
        # يسمح للمستخدم فقط برؤية تفاعلاته أو تفاعلات مراجعة معينة
        user = self.request.user
        return ReviewInteraction.objects.filter(user=user)

    def perform_create(self, serializer):
        # ربط التفاعل بالمستخدم الحالي
        interaction = serializer.save(user=self.request.user)

        # إرسال إشعار للمستخدم الذي كتب المراجعة
        if interaction.review.user != self.request.user:  # لا ترسل إشعاراً إذا كان التفاعل من نفس المستخدم
            Notification.objects.create(
                user=interaction.review.user,
                message=f"تلقت مراجعتك تفاعلاً جديداً على منتج {interaction.review.product.name}.",
            )

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

###################
#### Notification ####
###################
class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        notification_data = [
            {
                "id": n.id,
                "message": n.message,
                "related_review": n.related_review.id if n.related_review else None,
                "created_at": n.created_at,
            }
            for n in notifications
        ]

        return Response(notification_data)

    def post(self, request):
        # تحديث حالة الإشعارات إلى مقروءة
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return Response({"status": "All notifications marked as read."})
    

# =============================
# ✅ Admin Insights & Reports System
# =============================
class AdminReportView(APIView):
    """Admin Insights System - Comprehensive reporting for product reviews"""
    permission_classes = [IsAuthenticated, IsProductOwner]

    def get(self, request, *args, **kwargs):
        """
        Get comprehensive admin insights including:
        - Unapproved reviews count
        - Low-rated reviews (1-2 stars)
        - Reviews with offensive content
        - Detailed filtering options
        """
        try:
            # Get user's products
            user_products = Product.objects.filter(user=request.user)
            product_ids = user_products.values_list('id', flat=True)
            
            # Get all reviews for user's products
            all_reviews = Review.objects.filter(product_id__in=product_ids)
            
            # 1. Unapproved reviews (pending approval)
            unapproved_reviews = all_reviews.filter(is_visible=False)
            unapproved_count = unapproved_reviews.count()
            
            # 2. Low-rated reviews (1-2 stars)
            low_rated_reviews = all_reviews.filter(rating__in=[1, 2])
            low_rated_count = low_rated_reviews.count()
            
            # 3. Reviews with offensive content
            offensive_reviews = []
            for review in all_reviews:
                if review.contains_bad_words():
                    offensive_reviews.append(review)
            offensive_count = len(offensive_reviews)
            
            # 4. Get filter parameters from request
            filter_type = request.query_params.get('filter', 'all')
            product_id = request.query_params.get('product_id')
            rating_filter = request.query_params.get('rating')
            date_from = request.query_params.get('date_from')
            date_to = request.query_params.get('date_to')
            
            # Apply filters based on request
            filtered_reviews = all_reviews
            
            if product_id:
                filtered_reviews = filtered_reviews.filter(product_id=product_id)
            
            if rating_filter:
                filtered_reviews = filtered_reviews.filter(rating=rating_filter)
            
            if date_from:
                filtered_reviews = filtered_reviews.filter(created_at__gte=date_from)
            
            if date_to:
                filtered_reviews = filtered_reviews.filter(created_at__lte=date_to)
            
            # Apply specific filter types
            if filter_type == 'unapproved':
                filtered_reviews = filtered_reviews.filter(is_visible=False)
            elif filter_type == 'low_rated':
                filtered_reviews = filtered_reviews.filter(rating__in=[1, 2])
            elif filter_type == 'offensive':
                offensive_review_ids = [r.id for r in all_reviews if r.contains_bad_words()]
                filtered_reviews = filtered_reviews.filter(id__in=offensive_review_ids)
            
            # Prepare response data
            response_data = {
                'summary': {
                    'total_reviews': all_reviews.count(),
                    'unapproved_reviews': unapproved_count,
                    'low_rated_reviews': low_rated_count,
                    'offensive_reviews': offensive_count,
                    'approved_reviews': all_reviews.filter(is_visible=True).count(),
                },
                'filtered_reviews': ReviewSerializer(filtered_reviews, many=True).data,
                'filter_applied': filter_type,
                'products': [
                    {
                        'id': product.id,
                        'name': product.name,
                        'review_count': product.reviews.count(),
                        'avg_rating': self._calculate_avg_rating(product.reviews.filter(is_visible=True))
                    }
                    for product in user_products
                ]
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Error generating admin report: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculate_avg_rating(self, reviews):
        """Calculate average rating for a set of reviews"""
        if not reviews.exists():
            return 0
        return round(sum(review.rating for review in reviews) / reviews.count(), 1)


class AdminReviewActionView(APIView):
    """Admin actions for managing reviews (approve, reject, flag)"""
    permission_classes = [IsAuthenticated, IsProductOwner]

    def post(self, request, review_id, action):
        """
        Perform admin actions on reviews:
        - approve: Make review visible
        - reject: Mark review as rejected
        - flag: Flag review for offensive content
        """
        try:
            review = Review.objects.get(id=review_id)
            
            # Check if user owns the product
            if review.product.user != request.user:
                return Response(
                    {'error': 'You are not authorized to manage this review'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if action == 'approve':
                review.is_visible = True
                review.save()
                
                # Create notification for user
                Notification.objects.create(
                    user=review.user,
                    message=f"Your review for '{review.product.name}' has been approved and is now visible."
                )
                
                return Response({
                    'message': 'Review approved successfully',
                    'review_id': review.id
                }, status=status.HTTP_200_OK)
                
            elif action == 'reject':
                review.is_visible = False
                review.save()
                
                # Create admin report
                AdminReport.objects.create(
                    review=review,
                    status='rejected'
                )
                
                # Create notification for user
                Notification.objects.create(
                    user=review.user,
                    message=f"Your review for '{review.product.name}' has been rejected."
                )
                
                return Response({
                    'message': 'Review rejected successfully',
                    'review_id': review.id
                }, status=status.HTTP_200_OK)
                
            elif action == 'flag':
                # Create admin report for offensive content
                AdminReport.objects.create(
                    review=review,
                    status='pending'
                )
                
                return Response({
                    'message': 'Review flagged for review',
                    'review_id': review.id
                }, status=status.HTTP_200_OK)
                
            else:
                return Response(
                    {'error': 'Invalid action. Use: approve, reject, or flag'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Review.DoesNotExist:
            return Response(
                {'error': 'Review not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error performing action: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AdminDashboardView(APIView):
    """Admin dashboard with comprehensive insights and charts data"""
    permission_classes = [IsAuthenticated, IsProductOwner]

    def get(self, request):
        """
        Get comprehensive dashboard data including:
        - Review statistics over time
        - Rating distribution
        - Product performance metrics
        - Recent activity
        """
        try:
            # Get user's products
            user_products = Product.objects.filter(user=request.user)
            product_ids = user_products.values_list('id', flat=True)
            
            # Get all reviews for user's products
            all_reviews = Review.objects.filter(product_id__in=product_ids)
            
            # Calculate rating distribution
            rating_distribution = {}
            for rating in range(1, 6):
                count = all_reviews.filter(rating=rating).count()
                rating_distribution[f'{rating}_stars'] = count
            
            # Get reviews by month (last 6 months)
            from datetime import datetime, timedelta
            from django.utils import timezone
            
            monthly_stats = []
            for i in range(6):
                date = timezone.now() - timedelta(days=30*i)
                month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
                
                month_reviews = all_reviews.filter(created_at__range=[month_start, month_end])
                monthly_stats.append({
                    'month': month_start.strftime('%Y-%m'),
                    'total_reviews': month_reviews.count(),
                    'approved_reviews': month_reviews.filter(is_visible=True).count(),
                    'avg_rating': self._calculate_avg_rating(month_reviews.filter(is_visible=True))
                })
            
            # Get top performing products
            top_products = []
            for product in user_products:
                product_reviews = product.reviews.filter(is_visible=True)
                if product_reviews.exists():
                    avg_rating = self._calculate_avg_rating(product_reviews)
                    top_products.append({
                        'id': product.id,
                        'name': product.name,
                        'avg_rating': avg_rating,
                        'review_count': product_reviews.count(),
                        'recent_reviews': product_reviews.order_by('-created_at')[:5].count()
                    })
            
            # Sort by average rating
            top_products.sort(key=lambda x: x['avg_rating'], reverse=True)
            
            # Get recent activity
            recent_reviews = all_reviews.order_by('-created_at')[:10]
            
            response_data = {
                'overview': {
                    'total_products': user_products.count(),
                    'total_reviews': all_reviews.count(),
                    'approved_reviews': all_reviews.filter(is_visible=True).count(),
                    'pending_reviews': all_reviews.filter(is_visible=False).count(),
                    'overall_avg_rating': self._calculate_avg_rating(all_reviews.filter(is_visible=True))
                },
                'rating_distribution': rating_distribution,
                'monthly_stats': monthly_stats,
                'top_products': top_products[:5],  # Top 5 products
                'recent_activity': ReviewSerializer(recent_reviews, many=True).data,
                'alerts': {
                    'unapproved_count': all_reviews.filter(is_visible=False).count(),
                    'low_rated_count': all_reviews.filter(rating__in=[1, 2]).count(),
                    'offensive_count': len([r for r in all_reviews if r.contains_bad_words()])
                }
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Error generating dashboard: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculate_avg_rating(self, reviews):
        """Calculate average rating for a set of reviews"""
        if not reviews.exists():
            return 0
        return round(sum(review.rating for review in reviews) / reviews.count(), 1)






