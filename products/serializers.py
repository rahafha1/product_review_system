from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Product, Review
from django.contrib.auth.hashers import make_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
       model = User
       fields = ['username', 'email', 'password']

    def validate_password(self, value):
        return make_password(value)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'  # يشمل جميع الحقول
    def get_average_rating(self, obj):
        visible_reviews = obj.reviews.filter(is_visible=True)
        if visible_reviews.exists():
            return round(sum(review.rating for review in visible_reviews) / visible_reviews.count(), 1)
        return 0

    def get_review_count(self, obj):
        return obj.reviews.filter(is_visible=True).count()

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
