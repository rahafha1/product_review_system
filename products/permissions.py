
from rest_framework import permissions
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    يسمح فقط لمُنشئ المراجعة (أو المنتج في حال استخدم مع Product) بالتعديل أو الحذف.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        # التحقق من أن المستخدم مسجل
        if not request.user or not request.user.is_authenticated:
            return False

        # تحديد إذا كان المستخدم هو صاحب المراجعة أو المنتج
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'product') and hasattr(obj.product, 'user'):
            return obj.product.user == request.user

        return False


from rest_framework.permissions import BasePermission
from products.models import Product, Review

class IsProductOwner(BasePermission):
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        # إذا في باراميتر اسمه review_id، نتحقق إنو المراجعة تعود لمنتج يملكه المستخدم
        review_id = view.kwargs.get('review_id')
        if review_id:
            try:
                review = Review.objects.get(id=review_id)
                return review.product.user == user
            except Review.DoesNotExist:
                return False

        # أو إذا طلبنا /admin/dashboard أو /admin/reports → نتحقق إذا عنده منتجات
        if Product.objects.filter(user=user).exists():
            return True

        return False
  

