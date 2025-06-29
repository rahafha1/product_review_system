from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from .models import Product, Review, ReviewInteraction, Notification, AdminReport



# ✅ User Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def validate_password(self, value):
        """تشفير كلمة المرور قبل الحفظ"""
        return make_password(value)


# ✅ Product Serializer
class ProductSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField(read_only=True)
    review_count = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "description",
            "created_at",
            "user",
            "average_rating",
            "review_count",
        ]
        read_only_fields = ["id", "created_at", "user"]

    def get_average_rating(self, obj):
        visible_reviews = obj.reviews.filter(is_visible=True)
        if visible_reviews.exists():
            return round(sum(review.rating for review in visible_reviews) / visible_reviews.count(), 1)
        return 0

    def get_review_count(self, obj):
        return obj.reviews.filter(is_visible=True).count()


# ✅ Review Serializer
class ReviewSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    likes_count = serializers.SerializerMethodField()
    helpful_count = serializers.SerializerMethodField()
    class Meta:
        model = Review
        fields = ["id", "user", "rating", "review_text", "is_visible", "created_at","likes_count","helpful_count"]
        read_only_fields = ["id", "user", "created_at", "is_visible"]

    def validate_rating(self, value):
        """القيم من 1 إلى 5"""
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value
    
    def get_likes_count(self, obj):
        return obj.interactions.filter(liked=True).count()

    def get_helpful_count(self, obj):
        return obj.interactions.filter(is_helpful=True).count()


# ✅ ReviewInteraction Serializer by rahaf
class ReviewInteractionSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    helpful_count = serializers.SerializerMethodField()

    class Meta:
        model = ReviewInteraction
        fields = ['id', 'review', 'is_helpful', 'liked', 'created_at', 'likes_count', 'helpful_count']
        read_only_fields = ['created_at', 'likes_count', 'helpful_count']

    def get_likes_count(self, obj):
        return ReviewInteraction.objects.filter(review=obj.review, liked=True).count()

    def get_helpful_count(self, obj):
        return ReviewInteraction.objects.filter(review=obj.review, is_helpful=True).count()

    def validate(self, data):
        user = self.context["request"].user
        review = data.get("review", None) or getattr(self.instance, "review", None)

        if review and review.user == user:
            raise serializers.ValidationError("لا يمكنك التفاعل على مراجعتك.")

        # فقط إذا هو إنشاء (self.instance = None)
        if self.instance is None:
            # هل يوجد تفاعل سابق لنفس المستخدم والمراجعة؟
            if ReviewInteraction.objects.filter(review=review, user=user).exists():
                raise serializers.ValidationError("لقد تفاعلت مع هذه المراجعة مسبقًا.")

        return data

# ✅ Notification Serializer
class NotificationSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Notification
        fields = ["id", "user", "message", "is_read", "created_at"]
        read_only_fields = ["id", "user", "created_at"]


# ✅ AdminReport Serializer
class AdminReportSerializer(serializers.ModelSerializer):
    review = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = AdminReport
        fields = ["id", "review", "status", "created_at"]
        read_only_fields = ["id", "review", "created_at"]
