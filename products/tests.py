from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import Product, Review

class ReviewsAPITestCase(APITestCase):
    def setUp(self):
        # إنشاء مستخدمين
        self.user1 = User.objects.create_user(username='user1', password='pass1234')
        self.user2 = User.objects.create_user(username='user2', password='pass1234')

        # إنشاء منتج
        self.product = Product.objects.create(
            name="Test Product",
            description="A product for testing",
            price=9.99,
            user=self.user1  # المستخدم الأول هو المالك
        )

        # تهيئة العميل
        self.client = APIClient()

    def authenticate(self, user):
        """Helper to login a user and get auth token"""
        self.client.force_authenticate(user=user)

    def test_1_create_review(self):
        """اختبار إضافة مراجعة جديدة"""
        self.authenticate(self.user1)
        url = reverse('review-list', kwargs={'product_id': self.product.id})
        data = {
            'rating': 5,
            'review_text': 'Awesome product!'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Review.objects.count(), 1)

    def test_2_list_reviews(self):
        """اختبار عرض المراجعات المعتمدة فقط"""
        Review.objects.create(product=self.product, user=self.user1, rating=4, review_text='Good one!', is_visible=True)
        url = reverse('review-list', kwargs={'product_id': self.product.id})
        self.authenticate(self.user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_3_update_own_review(self):
        """اختبار تعديل مراجعة من قبل كاتبها"""
        review = Review.objects.create(product=self.product, user=self.user1, rating=3, review_text='Okay.')
        url = reverse('review-detail', kwargs={'product_id': self.product.id, 'review_id': review.id})
        self.authenticate(self.user1)
        data = {'review_text': 'Updated text'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertEqual(review.review_text, 'Updated text')

    def test_4_delete_own_review(self):
        """اختبار حذف مراجعة من قبل كاتبها"""
        review = Review.objects.create(product=self.product, user=self.user1, rating=3, review_text='Okay.')
        url = reverse('review-detail', kwargs={'product_id': self.product.id, 'review_id': review.id})
        self.authenticate(self.user1)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Review.objects.filter(id=review.id).exists())

    def test_5_approve_review(self):
        """اختبار موافقة مالك المنتج على مراجعة"""
        review = Review.objects.create(
            product=self.product,
            user=self.user2,  # كاتب المراجعة ليس المالك
            rating=2,
            review_text='Not good.',
            is_visible=False
        )
        url = reverse('approve-review', kwargs={'product_id': self.product.id, 'review_id': review.id})
        self.authenticate(self.user1)  # تسجيل الدخول كمالك المنتج
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertTrue(review.is_visible)

    def test_6_unauthorized_delete(self):
        """اختبار عدم قدرة مستخدم غير كاتب المراجعة على حذفها"""
        review = Review.objects.create(product=self.product, user=self.user2, rating=3, review_text='Another review.')
        url = reverse('review-detail', kwargs={'product_id': self.product.id, 'review_id': review.id})
        self.authenticate(self.user1)  # مستخدم غير كاتب المراجعة
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)