from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, ReviewViewSet

router = DefaultRouter()
router.register('products', ProductViewSet, basename='product')
router.register('reviews', ReviewViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
