from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .models import Product, Review, ReviewInteraction
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import TestCase
from rest_framework.test import APIClient

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

#### tests rahaf for interaction ####
class ReviewInteractionTests(APITestCase):
    def setUp(self):
        # إنشاء المستخدمين
        self.user1 = User.objects.create_user(username="user1", password="pass123")
        self.user2 = User.objects.create_user(username="user2", password="pass123")

        # إنشاء منتج ومراجعة تابعة له
        self.product = Product.objects.create(
            name="Test Product",
            description="Description",
            price=10.0,
            user=self.user1
        )
        self.review = Review.objects.create(
            product=self.product,
            user=self.user1,
            rating=5,
            review_text="Excellent product"
        )

        # إعداد توكنات
        self.token_user1 = str(RefreshToken.for_user(self.user1).access_token)
        self.token_user2 = str(RefreshToken.for_user(self.user2).access_token)

    def test_user_cannot_interact_with_own_review(self):
        """التفاعل على مراجعته مرفوض"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_user1}")

        response = self.client.post("/api/review-interactions/", {
            "review": self.review.id,
            "liked": True,
            "is_helpful": True
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_can_interact_with_others_review(self):
        """يمكن للمستخدم الثاني التفاعل على مراجعة غير مراجعته"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_user2}")

        response = self.client.post("/api/review-interactions/", {
            "review": self.review.id,
            "liked": True,
            "is_helpful": True
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_user_cannot_interact_twice_on_same_review(self):
        """ليس مسموحًا التفاعل مرتين على نفس المراجعة"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_user2}")

        self.client.post("/api/review-interactions/", {
            "review": self.review.id,
            "liked": True,
            "is_helpful": True
        }, format="json")

        second_response = self.client.post("/api/review-interactions/", {
            "review": self.review.id,
            "liked": True,
            "is_helpful": False
        }, format="json")

        self.assertEqual(second_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_interaction(self):
        """يمكن تعديل تفاعل موجود"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_user2}")

        create_response = self.client.post("/api/review-interactions/", {
            "review": self.review.id,
            "liked": True,
            "is_helpful": True
        }, format="json")

        interaction_id = create_response.data["id"]

        update_response = self.client.patch(f"/api/review-interactions/{interaction_id}/", {
            "liked": False,
            "is_helpful": False
        }, format="json")

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)

    def test_delete_interaction(self):
        """يمكن حذف التفاعل الحالي"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_user2}")

        create_response = self.client.post("/api/review-interactions/", {
            "review": self.review.id,
            "liked": True,
            "is_helpful": True
        }, format="json")

        interaction_id = create_response.data["id"]

        delete_response = self.client.delete(f"/api/review-interactions/{interaction_id}/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)

    def test_review_interaction_stats(self):
        """اختبار العد الإجمالي على مراجعة"""
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token_user2}")

        self.client.post("/api/review-interactions/", {
            "review": self.review.id,
            "liked": True,
            "is_helpful": True
        }, format="json")

        stats_response = self.client.get(f"/api/review-interactions/review/{self.review.id}/stats/")
        self.assertEqual(stats_response.status_code, status.HTTP_200_OK)
        self.assertIn("likes_count", stats_response.data)
        self.assertIn("helpful_count", stats_response.data)


class ProductTopReviewTests(TestCase):

    def setUp(self):
        # إنشاء مستخدم
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = APIClient()
        self.client.login(username="testuser", password="testpass")  # تسجيل الدخول
        # إنشاء منتج
        self.product = Product.objects.create(name="Product A", description="Test Product", user=self.user)

        # إنشاء مراجعات
        self.review1 = Review.objects.create(product=self.product, user=self.user, rating=5, review_text="Review 1", is_visible=True)
        self.review2 = Review.objects.create(product=self.product, user=self.user, rating=4, review_text="Review 2", is_visible=True)

        # تفاعل على review1 (2 liked, 1 helpful)
        ReviewInteraction.objects.create(review=self.review1, user=self.user, liked=True, is_helpful=True)

        another_user = User.objects.create_user(username="user2", password="pass123")
        ReviewInteraction.objects.create(review=self.review1, user=another_user, liked=True)

        # تفاعل على review2 (1 liked only)
        ReviewInteraction.objects.create(review=self.review2, user=self.user, liked=True)

    def test_top_review(self):
        """أفضل مراجعة يتم تحديدها على أساس التفاعل"""
        response = self.client.get(f"/api/products/{self.product.id}/top-review/")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        # review1 عندها 2 liked + 1 helpful => total_interactions = 3
        self.assertEqual(data["id"], self.review1.id)  # review1 لازم تكون الأفضل
        self.assertEqual(data["likes_count"], 2)       # review1
        self.assertEqual(data["helpful_count"], 1)     # review1