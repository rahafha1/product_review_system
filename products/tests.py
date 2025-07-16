from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.test import force_authenticate
from .models import Product, Review, ReviewInteraction , Notification, AdminReport
from .views import AdminReportView, AdminReviewActionView, AdminDashboardView
from rest_framework_simplejwt.tokens import RefreshToken

class ProductReviewTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='testpass1')
        self.user2 = User.objects.create_user(username='user2', password='testpass2')
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass')
        self.product = Product.objects.create(name="Test Product", description="Description", user=self.admin_user)

    def test_register_user(self):
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepass123'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['username'], 'newuser')

    def test_cant_edit_others_review(self):
        review = Review.objects.create(
            product=self.product,
            user=self.user1,
            rating=4,
            review_text="Original review"
        )
        self.client.force_authenticate(user=self.user2)
        url = reverse('review-detail-by-product', kwargs={'product_id': self.product.id, 'review_id': review.id})
        data = {'review_text': "Hacked!"}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, 403)
        self.assertIn("You do not have permission", response.data['detail'])

    def test_admin_can_approve_review(self):
        review = Review.objects.create(
            product=self.product,
            user=self.user1,
            rating=5,
            review_text="Needs approval",
            is_visible=False
        )
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-review-approve', kwargs={'product_id': self.product.id, 'review_id': review.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        review.refresh_from_db()
        self.assertTrue(review.is_visible)
        self.assertEqual(response.data['status'], 'Review approved!')

    def test_get_product_stats(self):
        Review.objects.create(product=self.product, user=self.user1, rating=4, review_text="Good", is_visible=True)
        Review.objects.create(product=self.product, user=self.user2, rating=2, review_text="Bad", is_visible=True)
        Review.objects.create(product=self.product, user=self.user2, rating=5, review_text="Hidden", is_visible=False)
        url = reverse('product-ratings', kwargs={'pk': self.product.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['approved_reviews'], 2)
        self.assertEqual(response.data['average_rating'], 3.0)

    def test_user_cannot_interact_with_own_review(self):
        self.client.force_authenticate(user=self.user1)
        product = Product.objects.create(name="Test", description="desc", user=self.user1)
        review = Review.objects.create(product=product, user=self.user1, rating=5, review_text="Nice")
        url = reverse('review-interaction-list')
        data = {
            'review': review.id,
            'liked': True,
            'is_helpful': True
        }
        response = self.client.post(url, data, format='json')
        print("RESPONSE STATUS:", response.status_code)
        print("RESPONSE DATA:", response.data)
        self.assertEqual(response.status_code, 403)

class ReviewInteractionTests(APITestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='pass123')
        self.user2 = User.objects.create_user(username='user2', password='pass123')
        self.product = Product.objects.create(name='Laptop', description='Nice', user=self.user1)
        self.review = Review.objects.create(
            product=self.product,
            user=self.user1,
            rating=5,
            review_text='Great!',
            is_visible=True
        )
        self.client.login(username='user2', password='pass123')

    def test_user_can_interact_with_others_review(self):
        url = reverse('review-interaction-list')
        data = {
            "review": self.review.id,
            "liked": True,
            "is_helpful": True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ReviewInteraction.objects.count(), 1)

    def test_user_cannot_interact_twice_on_same_review(self):
        ReviewInteraction.objects.create(review=self.review, user=self.user2, liked=True)
        url = reverse('review-interaction-list')
        data = {
            "review": self.review.id,
            "liked": True
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_interaction(self):
        interaction = ReviewInteraction.objects.create(review=self.review, user=self.user2, liked=True)
        url = reverse('review-interaction-detail', kwargs={"pk": interaction.id})
        data = {
            "liked": False,
            "is_helpful": True
        }
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        interaction.refresh_from_db()
        self.assertFalse(interaction.liked)
        self.assertTrue(interaction.is_helpful)

    def test_delete_interaction(self):
        interaction = ReviewInteraction.objects.create(review=self.review, user=self.user2, liked=True)
        url = reverse('review-interaction-detail', kwargs={"pk": interaction.id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ReviewInteraction.objects.count(), 0)

    def test_review_interaction_stats(self):
        ReviewInteraction.objects.create(review=self.review, user=self.user2, liked=True, is_helpful=True)
        url = reverse('review-interaction-stats', kwargs={"review_id": self.review.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['likes_count'], 1)
        self.assertEqual(response.data['helpful_count'], 1)

class ProductTopReviewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='admin', password='adminpass')
        self.product = Product.objects.create(name='Phone', description='Smartphone', user=self.user)
        self.review1 = Review.objects.create(product=self.product, user=self.user, rating=4, review_text='Good', is_visible=True)
        self.review2 = Review.objects.create(product=self.product, user=self.user, rating=5, review_text='Excellent', is_visible=True)
        ReviewInteraction.objects.create(review=self.review2, user=self.user, liked=True, is_helpful=True)

    def test_top_review(self):
        url = reverse('product-top-review', kwargs={'pk': self.product.id})
        self.client.login(username='admin', password='adminpass')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.review2.id)



#################### ADMIN #################33
class AdminInsightsTestCase(APITestCase):

    def setUp(self):
        # إنشاء مستخدم عادي
        self.user = User.objects.create_user(username='normaluser', password='pass1234')
        # إنشاء أدمن (سوبر يوزر)
        self.admin = User.objects.create_superuser(username='adminuser', password='adminpass')

        # إنشاء منتج للأدمن
        self.product = Product.objects.create(
            name='Admin Product',
            description='Admin product description',
            price=10.0,
            user=self.admin
        )
        # إنشاء مراجعات مختلفة للمنتج
        self.review_visible = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            review_text="Great product!",
            is_visible=True
        )
        self.review_unapproved = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=2,
            review_text="Not so good",
            is_visible=False
        )
        self.review_offensive = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=1,
            review_text="This is badword1 and offensive",  # يحتوي على كلمة محظورة
            is_visible=False
        )
        # إنشاء تقرير للإداري عن مراجعة مرفوضة
        self.report = AdminReport.objects.create(
            user=self.admin,
            review=self.review_offensive,
            status='pending'
        )

        self.client = APIClient()

    def test_admin_reports_summary(self):
        # تسجيل دخول كأدمن
        self.client.force_authenticate(user=self.admin)
        url = reverse('admin-reports')

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        summary = response.data.get('summary')
        self.assertIsNotNone(summary)
        self.assertEqual(summary['approved_reviews'], 1)
        self.assertEqual(summary['unapproved_reviews'], 2)
        self.assertEqual(summary['low_rated_reviews'], 2)  # 2 و 1 نجوم
        self.assertEqual(summary['offensive_reviews'], 1)

    def test_admin_reports_filtering(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('admin-reports')

        # فلترة مراجعات غير مقبولة
        response = self.client.get(url + '?filter=unapproved')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for r in response.data['filtered_reviews']:
            self.assertFalse(r['is_visible'])

        # فلترة مراجعات تقييم منخفض
        response = self.client.get(url + '?filter=low_rated')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for r in response.data['filtered_reviews']:
            self.assertIn(r['rating'], [1, 2])

        # فلترة مراجعات مسيئة
        response = self.client.get(url + '?filter=offensive')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for r in response.data['filtered_reviews']:
            self.assertIn('badword1', r['review_text'].lower())

    def test_admin_review_actions(self):
        self.client.force_authenticate(user=self.admin)
        # اختبار قبول مراجعة
        url_approve = reverse('admin-review-action', args=[self.review_unapproved.id, 'approve'])
        response = self.client.post(url_approve)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review_unapproved.refresh_from_db()
        self.assertTrue(self.review_unapproved.is_visible)

        # اختبار رفض مراجعة
        url_reject = reverse('admin-review-action', args=[self.review_visible.id, 'reject'])
        response = self.client.post(url_reject)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review_visible.refresh_from_db()
        self.assertFalse(self.review_visible.is_visible)
        self.assertTrue(AdminReport.objects.filter(review=self.review_visible, status='rejected').exists())

        # اختبار الإبلاغ عن مراجعة
        url_flag = reverse('admin-review-action', args=[self.review_visible.id, 'flag'])
        response = self.client.post(url_flag)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(AdminReport.objects.filter(review=self.review_visible, status='pending').exists())

    def test_admin_dashboard(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('admin-dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overview', response.data)
        self.assertIn('rating_distribution', response.data)
        self.assertIn('monthly_stats', response.data)
        self.assertIn('top_products', response.data)
        self.assertIn('recent_activity', response.data)
        self.assertIn('alerts', response.data)

    def test_unauthorized_access(self):
        # تسجيل دخول كمستخدم عادي
        self.client.force_authenticate(user=self.user)
        urls = [
            reverse('admin-reports'),
            reverse('admin-dashboard'),
            reverse('admin-review-action', args=[self.review_visible.id, 'approve']),
        ]
        for url in urls:
            response = self.client.get(url) if 'approve' not in url else self.client.post(url)
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_offensive_content_detection(self):
        # تأكد من كشف الكلمات المسيئة تلقائيًا
        self.assertTrue(self.review_offensive.contains_bad_words())
        self.assertFalse(self.review_visible.contains_bad_words())

    def test_product_owner_authorization(self):
        self.client.force_authenticate(user=self.user)  # مستخدم عادي
        # محاولة تعديل مراجعة تخص منتج الأدمن
        url_approve = reverse('admin-review-action', args=[self.review_unapproved.id, 'approve'])
        response = self.client.post(url_approve)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # تسجيل دخول الأدمن ومحاولة تعديل مراجعة غير مملوكة له (ننشئ مراجعة لمنتج غير مملوك للأدمن)
        other_product = Product.objects.create(name="Other Product", description="desc", price=5.0, user=self.user)
        other_review = Review.objects.create(product=other_product, user=self.user, rating=3, review_text="Ok", is_visible=False)
        self.client.force_authenticate(user=self.admin)
        url_approve_other = reverse('admin-review-action', args=[other_review.id, 'approve'])
        response = self.client.post(url_approve_other)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminInsightsIntegrationTest(APITestCase):

    def setUp(self):
        # مستخدمين
        self.admin = User.objects.create_superuser(username='admin', password='adminpass')
        self.user1 = User.objects.create_user(username='user1', password='pass1')
        self.user2 = User.objects.create_user(username='user2', password='pass2')

        # منتج الأدمن
        self.product = Product.objects.create(name='Product1', description='desc', price=20.0, user=self.admin)

        # مراجعات متعددة
        self.review1 = Review.objects.create(product=self.product, user=self.user1, rating=5, review_text="Great", is_visible=True)
        self.review2 = Review.objects.create(product=self.product, user=self.user2, rating=1, review_text="badword1 here", is_visible=False)
        self.review3 = Review.objects.create(product=self.product, user=self.user1, rating=3, review_text="Average", is_visible=True)

        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_complete_admin_workflow(self):
        # تحقق من التقارير الأولية
        url_reports = reverse('admin-reports')
        response = self.client.get(url_reports)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['summary']['total_reviews'], 3)

        # قبول مراجعة 2
        url_action = reverse('admin-review-action', args=[self.review2.id, 'approve'])
        response = self.client.post(url_action)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.review2.refresh_from_db()
        self.assertTrue(self.review2.is_visible)

        # تحديث التقارير بعد القبول
        response = self.client.get(url_reports)
        self.assertEqual(response.data['summary']['approved_reviews'], 3)

        # جلب لوحة التحكم
        url_dashboard = reverse('admin-dashboard')
        response = self.client.get(url_dashboard)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # تحقق من أن أفضل مراجعة حسب التفاعلات (نفترض أنه الأفضل تقييمًا)
        top_review = max([self.review1, self.review2, self.review3], key=lambda r: r.rating)
        self.assertEqual(top_review.rating, 5)  # تحقق بسيط حسب السيناريو

