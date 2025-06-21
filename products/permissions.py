# permissions.py

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



class IsProductOwner(permissions.BasePermission):
    """
    يسمح فقط لمُنشئ المنتج بتغيير حالة المراجعة (مثل الموافقة)
    """

    def has_object_permission(self, request, view, obj):
        # obj هنا هو المراجعة Review
        return obj.product.user == request.user
    
    