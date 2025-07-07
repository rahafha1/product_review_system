from datetime import timedelta
from django.db.models import Avg, Count, Q
from collections import Counter
import re
from django.utils import timezone
from products.models import Product, Review

# 1. تحليل متوسط تقييم المنتج أو جميع المنتجات خلال فترة زمنية
def get_product_rating_trend(product_id=None, days=30):
    """
    يحلل متوسط تقييم المنتج (أو جميع المنتجات إذا لم يتم تحديد المنتج) خلال فترة زمنية محددة.
    """
    start_date = timezone.now() - timedelta(days=days)
    filters = { 'created_at__gte': start_date}
    if product_id:
        filters['product_id'] = product_id
    reviews = Review.objects.filter(**filters)
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    total_reviews = reviews.count()
    return {
        'average_rating': round(avg_rating, 2),
        'total_reviews': total_reviews,
        'trend_days': days,
    }

# 2. الكلمات الأكثر شيوعًا في مراجعات منتج أو جميع المنتجات
def get_most_common_words_in_reviews(product_id=None, limit=10):
    """
    يحلل الكلمات الأكثر شيوعًا في مراجعات منتج معين أو جميع المنتجات.
    """
    filters = {}
    if product_id:
        filters['product_id'] = product_id
    reviews = Review.objects.filter(**filters)
    all_text = ' '.join([r.review_text.lower() for r in reviews])
    words = re.findall(r'\b\w{4,}\b', all_text)
    common_words = Counter(words).most_common(limit)
    return common_words

# 3. أكثر المستخدمين كتابةً للمراجعات
def get_top_reviewers(limit=5):
    """
    يعرض أكثر المستخدمين كتابةً للمراجعات.
    """
    top_users = Review.objects.values('user__username').annotate(
        count=Count('id')
    ).order_by('-count')[:limit]
    return [{'username': item['user__username'], 'review_count': item['count']} for item in top_users]

# 4. البحث في المراجعات باستخدام كلمات مفتاحية
def search_reviews_by_keyword(product_id=None, keyword=None):
    """
    يبحث عن المراجعات باستخدام كلمة مفتاحية في منتج معين أو جميع المنتجات.
    """
    if not keyword:
        return []
    filters = { 'review_text__icontains': keyword}
    if product_id:
        filters['product_id'] = product_id
    return Review.objects.filter(**filters).select_related('user')

# 5. تصدير المراجعات إلى CSV
import csv
from django.http import HttpResponse

def export_reviews_to_csv(reviews_queryset):
    """
    يصدر المراجعات إلى ملف CSV.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reviews.csv"'
    writer = csv.writer(response)
    writer.writerow(['ID', 'المستخدم', 'التقييم', 'نص المراجعة'])
    for review in reviews_queryset:
        writer.writerow([review.id, review.user.username, review.rating, review.review_text])
    return response

# 6. المنتجات الأعلى تقييمًا
def get_top_rated_products(days=30, limit=5):
    """
    يعرض المنتجات الأعلى تقييمًا خلال فترة زمنية محددة.
    """
    start_date = timezone.now() - timedelta(days=days)
    products = Product.objects.filter(
        reviews__created_at__gte=start_date,
        
    ).annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')[:limit]
    return [{'product_id': product.id, 'name': product.name, 'avg_rating': round(product.avg_rating, 2)} for product in products]

# 7. المراجعات منخفضة التقييم
def get_low_rating_reviews(product_id=None, limit=10):
    """
    يعرض المراجعات منخفضة التقييم لمنتج معين أو جميع المنتجات.
    """
    filters = { 'rating__lte': 2}
    if product_id:
        filters['product_id'] = product_id
    reviews = Review.objects.filter(**filters)[:limit]
    return [{'review_id': review.id, 'user': review.user.username, 'rating': review.rating, 'review_text': review.review_text} for review in reviews]

# 8. عدد المراجعات غير الموافق عليها
def get_pending_reviews_count():
    """
    يعرض عدد المراجعات غير الموافق عليها.
    """
    count = Review.objects.filter(is_visible=False).count()
    return {'pending_reviews': count}

# 9. تصفية المراجعات المسيئة
def filter_inappropriate_reviews(product_id=None, banned_words=[]):
    """
    يفلتر المراجعات المسيئة بناءً على الكلمات المحظورة.
    """
    filters = {}
    if product_id:
        filters['product_id'] = product_id
    reviews = Review.objects.filter(**filters)
    flagged_reviews = [
        {'review_id': review.id, 'user': review.user.username, 'review_text': review.review_text}
        for review in reviews
        if any(banned_word in review.review_text.lower() for banned_word in banned_words)
    ]
    return flagged_reviews
 