from rest_framework import viewsets, permissions
from .models import Product, Review
from .serializers import ProductSerializer, ReviewSerializer
from .permissions import IsOwnerOrReadOnly, IsAdminForApproval

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    # يمكن لأي أحد مشاهدة المنتجات، لكن الإضافة أو التعديل تتطلب تسجيل الدخول


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        """
        نحدد صلاحيات مختلفة حسب نوع العملية
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'approve_review':
            permission_classes = [permissions.IsAuthenticated, IsAdminForApproval]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        # عند إنشاء مراجعة، نعطيه المستخدم الحالي آلياً
        serializer.save(user=self.request.user)

    # الآن نضيف endpoint خاص بالموافقة للمشرفين
    from rest_framework.decorators import action
    from rest_framework.response import Response

    @action(detail=True, methods=['post'])
    def approve_review(self, request, pk=None):
        review = self.get_object()
        review.is_visible = True
        review.save()
        return Response({'status': 'Review approved!'})
