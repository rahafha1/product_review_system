from django.db import models
from django.contrib.auth.models import User

# ✅ قائمة الكلمات المحظورة
BAD_WORDS = ["badword1", "badword2", "offensive"]

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Review(models.Model):
    STAR_CHOICES = [
        (1, '⭐'),
        (2, '⭐⭐'),
        (3, '⭐⭐⭐'),
        (4, '⭐⭐⭐⭐'),
        (5, '⭐⭐⭐⭐⭐'),
    ]
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE)
    rating = models.IntegerField(choices=STAR_CHOICES)
    review_text = models.TextField()
    is_visible = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def contains_bad_words(self):
        """Check if review contains any bad words."""
        text_lower = self.review_text.lower()
        return any(bad_word in text_lower for bad_word in BAD_WORDS)

    def __str__(self):
        return f"{self.product.name} - {self.rating} Stars by {self.user.username}"


# ✅ الجدول الجديد (التفاعل على المراجعات): like/helpful
class ReviewInteraction(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="interactions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="review_interactions")
    is_helpful = models.BooleanField(default=False)  # True يعني "مفيد"
    liked = models.BooleanField(default=False)        # True يعني "تم الإعجاب"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'user')


# ✅ الجدول الجديد (الإشعارات): يتم استخدامه عند الموافقة على مراجعة أو تلقي تفاعل
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"


# ✅ الجدول الجديد (تقارير المشرف): مراجعات مرفوضة، تحتوي كلمات محظورة، تقييم منخفض
class AdminReport(models.Model):
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name="reports")
    status = models.CharField(max_length=20, choices=[
        ("pending", "Pending"),
        ("rejected", "Rejected")
    ], default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for review {self.review.id} - Status: {self.status}"
