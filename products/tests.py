from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .models import Product, Review


class ProductReviewAPITest(APITestCase):

    def setUp(self):
        # إنشاء مستخدم ومشرف
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.admin = User.objects.create_superuser(username='admin', password='adminpass')
        # إنشاء منتج مرتبط بالمشرف
        self.product = Product.objects.create(
            name="Test Product",
            description="Description",
            price=100,
            user=self.admin
        )
        # الحصول على توكن للمستخدم
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.access_token = response.data['access']

    def authenticate(self, token=None):
        """ توثيق الطلب """
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + (token or self.access_token))

    def test_register_user(self):
        """ ✅ اختبار تسجيل مستخدم """
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cant_edit_others_review(self):
        """ ❌ اختبار عدم إمكانية تعديل مراجعة لآخر """
        review = Review.objects.create(
            product=self.product,
            user=self.admin,
            rating=4,
            review_text='Old comment'
        )
        self.authenticate()
        url = reverse('review-detail', args=[review.id])
        response = self.client.put(url, {'rating': 5, 'review_text': 'New comment'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_approve_review(self):
        """ ✅ اختبار إمكانية الموافقة على مراجعة من قبل المشرف """
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            review_text='Nice product',
            is_visible=False
        )
        # توثيق الدخول بالمشرف
        admin_token = self.client.post(reverse('token_obtain_pair'), {
            'username': 'admin',
            'password': 'adminpass'
        }).data['access']
        self.authenticate(token=admin_token)

        url = reverse('admin-review-approve', args=[review.id])
        response = self.client.post(url)
        review.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(review.is_visible)

    def test_get_product_stats(self):
        """ ✅ اختبار حساب متوسط التقييم وعدد المراجعات المعتمدة """
        Review.objects.create(product=self.product, user=self.user, rating=5, review_text='Great!', is_visible=True)
        Review.objects.create(product=self.product, user=self.admin, rating=4, review_text='Good.', is_visible=True)

        url = reverse('product-ratings', args=[self.product.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['average_rating'], 4.5)
        self.assertEqual(response.data['approved_reviews'], 2)
