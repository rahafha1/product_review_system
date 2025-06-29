from datetime import timedelta
from django.db.models import Avg, Count
from collections import Counter
import re

from products.models import Review,Product


def get_product_rating_trend(product_id, days=30):
    from django.utils import timezone

    start_date = timezone.now() - timedelta(days=days)

    reviews = Review.objects.filter(
        product_id=product_id,
        is_visible=True,
        created_at__gte=start_date
    )

    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    total_reviews = reviews.count()

    return {
        'average_rating': round(avg_rating, 2),
        'total_reviews': total_reviews,
        'trend_days': days
    }


def get_most_common_words_in_reviews(product_id, limit=10):
    reviews = Review.objects.filter(product_id=product_id, is_visible=True)
    all_text = ' '.join([r.review_text.lower() for r in reviews])
    words = re.findall(r'\b\w{4,}\b', all_text)  # الكلمات التي طولها 4 أحرف فأكثر
    common_words = Counter(words).most_common(limit)
    return common_words


def get_top_reviewers(limit=5):
    top_users = Review.objects.values('user__username').annotate(
        count=Count('id')
    ).order_by('-count')[:limit]

    return [
        {'username': item['user__username'], 'review_count': item['count']}
        for item in top_users
    ]


def search_reviews_by_keyword(product_id, keyword):
    """
    البحث عن مراجعات تحتوي على كلمة مفتاحية معينة
    """
    if not keyword:
        return []

    return Review.objects.filter(
        product_id=product_id,
        is_visible=True,
        review_text__icontains=keyword
    ).select_related('user')  # لتحسين الأداء عند الوصول للمستخدم



####التصدير الى ملف
####
import csv
from django.http import HttpResponse

def export_reviews_to_csv(reviews_queryset):
    """
    تصدير قائمة مراجعات إلى ملف CSV
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reviews.csv"'

    writer = csv.writer(response)
    writer.writerow(['ID', 'المستخدم', 'التقييم', 'نص المراجعة'])

    for review in reviews_queryset:
        writer.writerow([
            review.id,
            review.user.username,
            review.rating,
            review.review_text
        ])

    return response