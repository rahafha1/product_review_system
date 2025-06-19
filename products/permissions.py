from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    يسمح فقط لصاحب المراجعة بالتعديل أو الحذف.
    """

    def has_object_permission(self, request, view, obj):
        # السماح للقراءة دائماً
        if request.method in permissions.SAFE_METHODS:
            return True

        # السماح بالتعديل والحذف فقط لصاحب المراجعة
        return obj.user == request.user


class IsAdminForApproval(permissions.BasePermission):
    """
    يسمح فقط للمشرف بتعديل حالة is_visible.
    """

    def has_permission(self, request, view):
        # المشرف فقط له الصلاحية
        return request.user and request.user.is_staff
