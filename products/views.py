from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from .models import Product, Review, Notification, AdminReport ,ReviewComment
from .serializers import ProductSerializer, ReviewSerializer, UserSerializer ,ReviewInteraction , ReviewInteractionSerializer ,ReviewCommentSerializer
from .permissions import IsOwnerOrReadOnly, IsProductOwner
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, AllowAny , IsAdminUser , IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied, NotFound
from django.db.models import Count, Q , F
from datetime import datetime, timedelta
from django.utils import timezone

####################### register ######################
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
        
        #################### product ####################
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    def get_permissions(self):
            if self.action in ['create']:   # فقط إنشاء المنتج
                permission_classes = [IsAdminUser]  # فقط الأدمن يضيف منتجات
            elif self.action in ['update', 'partial_update', 'destroy']:
                permission_classes = [IsAdminUser]
            else:
                permission_classes = [permissions.IsAuthenticatedOrReadOnly]
            return [perm() for perm in permission_classes]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

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
    
    ######################## reviews  ###################3 

class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['rating']
    search_fields = ['review_text']
    ordering_fields = ['created_at', 'rating', 'likes_count', 'helpful_count']
    def get_queryset(self):
        product_id = self.kwargs['product_id']
        queryset = Review.objects.filter(product_id=product_id, is_visible=True)
        rating = self.request.query_params.get('rating') #تصفية حسب التقييم
        if rating:
            try:
                rating = int(rating)
                if 1 <= rating <= 5:
                    queryset = queryset.filter(rating=rating)
            except ValueError:
                pass
        order_by = self.request.query_params.get('ordering') #ترتيب حسب نوع معين
        if order_by:
            if order_by == 'most_interactions':
                queryset = queryset.annotate(
                    total_interactions=F('likes_count') + F('helpful_count')
                ).order_by('-total_interactions')
            else:
                try:
                    queryset = queryset.order_by(order_by)
                except Exception:
                    pass  # تجاهل القيم غير الصحيحة
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

class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsOwnerOrReadOnly]
    lookup_url_kwarg = 'review_id'
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
    
        # زيادة عدد المشاهدات
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
    
        # حساب عدد التفاعلات
        likes_count = instance.interactions.filter(liked=True).count()
        helpful_count = instance.interactions.filter(is_helpful=True).count()

        # تحقق إذا المستخدم تفاعل أو بلغ
        user = request.user
        user_liked = False
        reported = False
        if user.is_authenticated:
            user_liked = instance.interactions.filter(user=user, liked=True).exists()
            reported = AdminReport.objects.filter(review=instance, user=user).exists()

        # تجهيز البيانات
        serializer = self.get_serializer(instance)
        data = serializer.data.copy()
        data.update({
            'views_count': instance.views_count,
            'user_liked': user_liked,
            'reported': reported,
            'likes_count': likes_count,
            'helpful_count': helpful_count
        })
        ## يعرض التعليقات عالمراجعة مع تفاصيلها 
        comments = ReviewComment.objects.filter(review=instance).order_by('-created_at')
        comments_data = ReviewCommentSerializer(comments, many=True).data
        data.update({
            'comments': comments_data
        })
        return Response(data)

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

class ApproveReviewView(APIView): ####### (Admin only)
    permission_classes = [IsAuthenticated, IsProductOwner]

    def post(self, request, product_id, review_id):
        try:
            review = Review.objects.get(id=review_id, product_id=product_id)
        except Review.DoesNotExist:
            return Response({'error': 'Review not found.'}, status=status.HTTP_404_NOT_FOUND)

        if review.product.user != request.user and not request.user.is_superuser:
            return Response({'error': 'You do not have permission to approve this review.'}, status=status.HTTP_403_FORBIDDEN)

        review.is_visible = True
        review.save()

        return Response({
            'status': 'Review approved!',
            'product_id': product_id,
            'review_id': review_id,
            'product_name': review.product.name
        }, status=status.HTTP_200_OK)

    ## لارسال تعليق على مراجعة  ####rahaf###
class AddCommentToReview(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, review_id):
        try:
            review = Review.objects.get(id=review_id)
        except Review.DoesNotExist:
            return Response({"error": "Review not found"}, status=404)
        
        comment_text = request.data.get('comment_text')
        if not comment_text:
            return Response({"error": "comment_text is required"}, status=400)
        
        comment = ReviewComment.objects.create(
            review=review,
            user=request.user,
            comment_text=comment_text
        )
        return Response(ReviewCommentSerializer(comment).data, status=201)

    ############################## interactions rahaf ####################

class ReviewInteractionViewSet(viewsets.ModelViewSet): 
    queryset = ReviewInteraction.objects.all()
    serializer_class = ReviewInteractionSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self): 
        # يسمح للمستخدم فقط برؤية تفاعلاته أو تفاعلات مراجعة معينة
        user = self.request.user
        return ReviewInteraction.objects.filter(user=user)
    def perform_create(self, serializer):
        if serializer.validated_data['review'].user == self.request.user:
            raise PermissionDenied("You cannot interact with your own review.")
        # ربط التفاعل بالمستخدم الحالي
        interaction = serializer.save(user=self.request.user)
        # إرسال إشعار للمستخدم الذي كتب المراجعة
        if interaction.review.user != self.request.user:  # لا ترسل إشعاراً إذا كان التفاعل من نفس المستخدم
            Notification.objects.create(
                user=interaction.review.user,
                message=f"تلقت مراجعتك تفاعلاً جديداً على منتج {interaction.review.product.name}.",
            )
    @action(detail=False, methods=['get'], url_path='review/(?P<review_id>[^/.]+)/stats', name='review-interaction-stats')
    def review_interaction_stats(self, request, review_id=None):
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
        try: # تأكد المنتج موجود
            product = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({"detail": "المنتج غير موجود."}, status=status.HTTP_404_NOT_FOUND)
        reviews = Review.objects.filter(product=product).annotate(   # جلب مراجعات المنتج مع حساب عدد الإعجابات وعدد التقييمات كمفيد ي
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
    
class ReviewCommentViewSet(viewsets.ModelViewSet):
    queryset = ReviewComment.objects.all()
    serializer_class = ReviewCommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def get_queryset(self):
        review_id = self.request.query_params.get('review_id')
        if review_id:
            return ReviewComment.objects.filter(review_id=review_id)
        return ReviewComment.objects.all()

    
######################## Notification ########################
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
    
########################### Admin Insights & Reports System #################################
class AdminReportView(APIView):  #Admin Insights System - Comprehensive reporting for product reviews
    permission_classes = [IsAuthenticated, IsProductOwner]
    def get(self, request, *args, **kwargs):
        #Get comprehensive admin insights including: Unapproved reviews count ,Low-rated reviews (1-2 stars) ,Reviews with offensive content ,Detailed filtering options
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
            response_data = { # Prepare response data
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
    def _calculate_avg_rating(self, reviews): #Calculate average rating for a set of reviews
        if not reviews.exists():
            return 0
        return round(sum(review.rating for review in reviews) / reviews.count(), 1)
class AdminReviewActionView(APIView):
    # Admin actions for managing reviews (approve, reject, flag)
    permission_classes = [IsAuthenticated, IsProductOwner]

    def post(self, request, review_id, action):
        try:
            review = Review.objects.get(id=review_id)
            if review.product.user != request.user:  # Check ownership
                return Response(
                    {'error': 'You are not authorized to manage this review'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            if action == 'approve':
                review.is_visible = True
                review.save()
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
                AdminReport.objects.create(
                    review=review,
                    status='rejected',
                    user=request.user
                )
                Notification.objects.create(
                    user=review.user,
                    message=f"Your review for '{review.product.name}' has been rejected."
                )
                return Response({
                    'message': 'Review rejected successfully',
                    'review_id': review.id
                }, status=status.HTTP_200_OK)

            elif action == 'flag':
                AdminReport.objects.create(
                    review=review,
                    status='pending',
                    user=request.user
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
            import traceback
            print(f"Error in AdminReviewActionView: {str(e)}")
            traceback.print_exc()
            return Response(
                {'error': f'Error performing action: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class AdminDashboardView(APIView): #Admin dashboard with comprehensive insights and charts data
    permission_classes = [IsAuthenticated, IsProductOwner]
    def get(self, request): # Get comprehensive dashboard data including: Review statistics over time,Rating distribution,Product performance metrics,Recent activity
        try:
            user_products = Product.objects.filter(user=request.user) # Get user's products
            product_ids = user_products.values_list('id', flat=True)
            all_reviews = Review.objects.filter(product_id__in=product_ids) # Get all reviews for user's products
            rating_distribution = {} # Calculate rating distribution
            for rating in range(1, 6):
                count = all_reviews.filter(rating=rating).count()
                rating_distribution[f'{rating}_stars'] = count
            monthly_stats = []  # Get reviews by month (last 6 months) 
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
            top_products = []  # Get top performing products
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
            top_products.sort(key=lambda x: x['avg_rating'], reverse=True)  # Sort by average rating
            recent_reviews = all_reviews.order_by('-created_at')[:10] # Get recent activity
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
    
    #############################  kinana analytics تحليلات ######################

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from products.analytics import (
    get_product_rating_trend,
    get_most_common_words_in_reviews,
    get_top_reviewers,
    search_reviews_by_keyword,
    export_reviews_to_csv,
    get_top_rated_products,
    get_low_rating_reviews,
    get_pending_reviews_count,
    filter_inappropriate_reviews
)
##جميع المنتجات
class AllProductsAnalyticsView(APIView):
    def get(self, request):
        all_products_data = [
            {
                "product_id": product.id,
                "name": product.name,
                "rating_trend": get_product_rating_trend(product.id),
                "most_common_words": get_most_common_words_in_reviews(product.id),
                "low_rating_reviews": get_low_rating_reviews(product.id),
                
            }
            for product in Product.objects.all()
        ]
        return Response({"products_analytics": all_products_data})
   #تحليل منتج
class ProductAnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, product_id=None):
        rating_data = get_product_rating_trend(product_id)
        common_words = get_most_common_words_in_reviews(product_id)
        low_rating_reviews = get_low_rating_reviews(product_id)
        inappropriate_reviews = filter_inappropriate_reviews(
            product_id, banned_words=['ugly', 'offensive']
        )
        pending_reviews_count = get_pending_reviews_count()
        return Response({
            "product_id": product_id,
            "rating_trend": rating_data,
            "most_common_words": common_words,
            "low_rating_reviews": low_rating_reviews,
            "inappropriate_reviews": inappropriate_reviews,
            "pending_reviews_count": pending_reviews_count
        })
# تحليل جميع المنتجات الأعلى تقييمًا
class TopRatedProductsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        days = int(request.GET.get('days', 30))  # عدد الأيام لتحليل التقييمات (افتراضي 30)
        top_products = get_top_rated_products(days=days)
        return Response({"top_rated_products": top_products})
# تحليل أكثر المستخدمين كتابةً للمراجعات
class TopReviewersView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        limit = int(request.GET.get('limit', 5))  
        top_reviewers = get_top_reviewers(limit=limit)
        return Response({"top_reviewers": top_reviewers})
# البحث في المراجعات باستخدام كلمات مفتاحية
class KeywordSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, product_id=None):
        keyword = request.GET.get('keyword', '').strip()
        if not keyword:
            return Response(
                {"error": "الرجاء إدخال كلمة مفتاحية باستخدام المعامل 'keyword'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        reviews = search_reviews_by_keyword(product_id, keyword)
        results = [
            {"id": r.id, "user": r.user.username, "rating": r.rating, "review_text": r.review_text}
            for r in reviews
        ]
        return Response({
            "product_id": product_id,
            "keyword": keyword,
            "results_count": len(results),
            "reviews": results
        })
# تصدير المراجعات إلى CSV
from django.http import HttpResponse
import csv
class ExportAllReviewsAnalyticsToCSV(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        # إعداد استجابة CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="all_reviews_analytics.csv"'
        writer = csv.writer(response, delimiter=',')  
        writer.writerow(['Product ID', 'Product Name', 'Average Rating', 'Total Reviews'])
        products = Product.objects.all()
        for product in products:
            reviews = product.reviews.all()
            total_reviews = reviews.count()
            avg_rating = (
                round(sum(review.rating for review in reviews) / total_reviews, 1)
                if total_reviews > 0
                else 0
            )
            writer.writerow([product.id  , product.name , avg_rating  , total_reviews])
        return response
######excel
from openpyxl import Workbook
from products.analytics import (
    get_product_rating_trend,
    get_most_common_words_in_reviews,
    get_low_rating_reviews,
    get_pending_reviews_count,
)
class ExportReviewsToExcel(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        wb = Workbook() # إنشاء ملف Excel جديد
        ws = wb.active
        ws.title = "Products Analytics"
        ws.append([     # كتابة رؤوس الأعمدة
            'Product ID', 'Product Name', 'Average Rating', 'Total Reviews',
            'Most Common Words', 'Low Rating Reviews', 'Pending Reviews Count'
        ])
        # جلب المنتجات وتحليل كل منتج
        products = Product.objects.all()
        for product in products:
            # التحليلات الخاصة بكل منتج
            rating_trend = get_product_rating_trend(product.id)
            most_common_words = get_most_common_words_in_reviews(product.id, limit=5)
            low_rating_reviews = get_low_rating_reviews(product.id, limit=5)
            pending_reviews_count = get_pending_reviews_count()
            most_common_words_str = ', '.join([f"{word}({count})" for word, count in most_common_words])
            low_rating_reviews_str = '; '.join([f"{review['review_text']}({review['rating']})" for review in low_rating_reviews])
            ws.append([
                product.id,
                product.name,
                rating_trend['average_rating'],
                rating_trend['total_reviews'],
                most_common_words_str,
                low_rating_reviews_str,
                pending_reviews_count['pending_reviews'],
            ])
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename=products_analytics.xlsx'
        wb.save(response)
        return response





