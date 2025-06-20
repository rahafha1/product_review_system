from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .models import Product, Review


class ProductReviewAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.admin = User.objects.create_superuser(username='admin', password='adminpass')
        self.product = Product.objects.create(name="Test Product", price=100, description="A test product")

        # تسجيل الدخول للحصول على توكن
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.access_token = response.data['access']

    def authenticate(self, token=None):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + (token or self.access_token))

    def test_register_user(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_login_user(self):
        response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'testuser',
            'password': 'testpass'
        })
        self.assertIn('access', response.data)

    def test_create_review_authenticated(self):
        self.authenticate()
        data = {
            'product': self.product.id,
            'rating': 5,
            'review_text': 'Great product!'
        }
        response = self.client.post(reverse('review-list-create', args=[self.product.id]), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_cant_edit_others_review(self):
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            review_text='Old comment'
        )

        other_user_data = {
            'rating': 5,
            'review_text': 'New comment'
        }

        self.authenticate()
        url = reverse('review-detail', args=[review.id])
        response = self.client.put(url, other_user_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_approve_review(self):
        review = Review.objects.create(
            product=self.product,
            user=self.user,
            rating=4,
            review_text='Nice product',
            is_visible=False
        )

        self.authenticate()
        url = reverse('review-approve_review', args=[review.id])
        response = self.client.post(url)
        review.refresh_from_db()
        self.assertTrue(review.is_visible)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_product_stats(self):
        Review.objects.create(
            product=self.product,
            user=self.user,
            rating=5,
            review_text='Great product',
            is_visible=True
        )
        Review.objects.create(
            product=self.product,
            user=self.admin,
            rating=4,
            review_text='Good product',
            is_visible=True
        )

        url = reverse('product-rating-info', args=[self.product.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['average_rating'], 4.5)
        self.assertEqual(response.data['approved_reviews'], 2)