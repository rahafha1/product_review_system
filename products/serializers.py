from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Product, Review

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'  # يشمل جميع الحقول


class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)  # يعرض اسم المستخدم فقط بدلاً من الـ ID
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ('created_at', 'is_visible')

    # تحقق مخصص للتقييم
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
