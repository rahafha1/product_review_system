
from .models import Product, Review, ReviewInteraction, Notification, AdminReport
from rest_framework_simplejwt.tokens import RefreshToken
from django.test import TestCase
from rest_framework.test import APIClient
from .views import AdminReportView, AdminReviewActionView, AdminDashboardView

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
        self.assertEqual(Review.objects.count(), 1)

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
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
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

class AdminInsightsTestCase(APITestCase):
    """Test cases for Admin Insights System (Task 8 - Number 4)"""
    
    def setUp(self):
        """Set up test data"""
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.regular_user = User.objects.create_user(
            username='regular_user',
            email='user@test.com',
            password='testpass123'
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Test Product 1',
            description='Test Description 1',
            price=99.99,
            user=self.admin_user
        )
        
        self.product2 = Product.objects.create(
            name='Test Product 2',
            description='Test Description 2',
            price=149.99,
            user=self.admin_user
        )
        
        # Create test reviews with different scenarios
        self.approved_review = Review.objects.create(
            product=self.product1,
            user=self.regular_user,
            rating=5,
            review_text='Great product! Highly recommended.',
            is_visible=True
        )
        
        self.unapproved_review = Review.objects.create(
            product=self.product1,
            user=self.regular_user,
            rating=4,
            review_text='Good product but needs improvement.',
            is_visible=False
        )
        
        self.low_rated_review = Review.objects.create(
            product=self.product2,
            user=self.regular_user,
            rating=1,
            review_text='Very bad product. Do not buy.',
            is_visible=True
        )
        
        self.offensive_review = Review.objects.create(
            product=self.product2,
            user=self.regular_user,
            rating=2,
            review_text='This product is badword1 and badword2.',
            is_visible=True
        )

    def test_admin_reports_summary(self):
        """Test admin reports summary endpoint"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/admin/reports/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        
        # Check summary data
        self.assertEqual(data['summary']['total_reviews'], 4)
        self.assertEqual(data['summary']['unapproved_reviews'], 1)
        self.assertEqual(data['summary']['low_rated_reviews'], 2)  # 1-star and 2-star reviews
        self.assertEqual(data['summary']['offensive_reviews'], 1)
        self.assertEqual(data['summary']['approved_reviews'], 3)

    def test_admin_reports_filtering(self):
        """Test admin reports with different filters"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test unapproved filter
        response = self.client.get('/admin/reports/?filter=unapproved')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['filtered_reviews']), 1)
        
        # Test low_rated filter
        response = self.client.get('/admin/reports/?filter=low_rated')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['filtered_reviews']), 2)
        
        # Test offensive filter
        response = self.client.get('/admin/reports/?filter=offensive')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['filtered_reviews']), 1)

    def test_admin_review_actions(self):
        """Test admin review actions (approve, reject, flag)"""
        self.client.force_authenticate(user=self.admin_user)
        
        # Test approve action
        response = self.client.post(f'/admin/reviews/{self.unapproved_review.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if review is now visible
        self.unapproved_review.refresh_from_db()
        self.assertTrue(self.unapproved_review.is_visible)
        
        # Check if notification was created
        notification = Notification.objects.filter(user=self.regular_user).first()
        self.assertIsNotNone(notification)
        self.assertIn('approved', notification.message)
        
        # Test reject action
        response = self.client.post(f'/admin/reviews/{self.approved_review.id}/reject/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if review is now hidden
        self.approved_review.refresh_from_db()
        self.assertFalse(self.approved_review.is_visible)
        
        # Check if admin report was created
        admin_report = AdminReport.objects.filter(review=self.approved_review).first()
        self.assertIsNotNone(admin_report)
        self.assertEqual(admin_report.status, 'rejected')
        
        # Test flag action
        response = self.client.post(f'/admin/reviews/{self.low_rated_review.id}/flag/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check if admin report was created
        admin_report = AdminReport.objects.filter(review=self.low_rated_review).first()
        self.assertIsNotNone(admin_report)
        self.assertEqual(admin_report.status, 'pending')

    def test_admin_dashboard(self):
        """Test admin dashboard with comprehensive insights"""
        self.client.force_authenticate(user=self.admin_user)
        
        response = self.client.get('/admin/dashboard/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data
        
        # Check overview data
        self.assertEqual(data['overview']['total_products'], 2)
        self.assertEqual(data['overview']['total_reviews'], 4)
        self.assertEqual(data['overview']['approved_reviews'], 3)
        self.assertEqual(data['overview']['pending_reviews'], 1)
        
        # Check rating distribution
        self.assertEqual(data['rating_distribution']['1_stars'], 1)
        self.assertEqual(data['rating_distribution']['2_stars'], 1)
        self.assertEqual(data['rating_distribution']['4_stars'], 1)
        self.assertEqual(data['rating_distribution']['5_stars'], 1)
        
        # Check alerts
        self.assertEqual(data['alerts']['unapproved_count'], 1)
        self.assertEqual(data['alerts']['low_rated_count'], 2)
        self.assertEqual(data['alerts']['offensive_count'], 1)

    def test_unauthorized_access(self):
        """Test that non-admin users cannot access admin endpoints"""
        self.client.force_authenticate(user=self.regular_user)
        
        # Try to access admin reports
        response = self.client.get('/admin/reports/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try to access admin dashboard
        response = self.client.get('/admin/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Try to perform admin action
        response = self.client.post(f'/admin/reviews/{self.approved_review.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_offensive_content_detection(self):
        """Test offensive content detection using bad words list"""
        # Test that offensive review is detected
        self.assertTrue(self.offensive_review.contains_bad_words())
        
        # Test that normal review is not detected as offensive
        self.assertFalse(self.approved_review.contains_bad_words())

    def test_product_owner_authorization(self):
        """Test that only product owners can manage their product reviews"""
        # Create another user with their own product
        other_user = User.objects.create_user(
            username='other_user',
            email='other@test.com',
            password='testpass123'
        )
        
        other_product = Product.objects.create(
            name='Other Product',
            description='Other Description',
            price=199.99,
            user=other_user
        )
        
        other_review = Review.objects.create(
            product=other_product,
            user=self.regular_user,
            rating=3,
            review_text='Average product.',
            is_visible=False
        )
        
        # Admin user should not be able to manage other user's product reviews
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(f'/admin/reviews/{other_review.id}/approve/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminInsightsIntegrationTest(TestCase):
    """Integration tests for admin insights system"""
    
    def setUp(self):
        """Set up integration test data"""
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.product = Product.objects.create(
            name='Integration Test Product',
            description='Test Description',
            price=99.99,
            user=self.admin_user
        )
    
    def test_complete_admin_workflow(self):
        """Test complete admin workflow from review creation to management"""
        # Create multiple reviews
        users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@test.com',
                password='testpass123'
            )
            users.append(user)
        
        # Create reviews with different scenarios
        reviews = []
        ratings = [1, 2, 3, 4, 5]
        texts = [
            'Very bad product badword1',
            'Not good at all',
            'Average product',
            'Good product',
            'Excellent product!'
        ]
        
        for i, (user, rating, text) in enumerate(zip(users, ratings, texts)):
            review = Review.objects.create(
                product=self.product,
                user=user,
                rating=rating,
                review_text=text,
                is_visible=(i >= 2)  # First 2 reviews are unapproved
            )
            reviews.append(review)
        
        # Test admin reports
        from .views import AdminReportView
        view = AdminReportView()
        view.request = type('Request', (), {'user': self.admin_user, 'query_params': {}})()
        
        # Simulate the get method logic
        user_products = Product.objects.filter(user=self.admin_user)
        product_ids = user_products.values_list('id', flat=True)
        all_reviews = Review.objects.filter(product_id__in=product_ids)
        
        # Verify counts
        self.assertEqual(all_reviews.count(), 5)
        self.assertEqual(all_reviews.filter(is_visible=False).count(), 2)
        self.assertEqual(all_reviews.filter(rating__in=[1, 2]).count(), 2)
        
        # Check offensive content
        offensive_count = sum(1 for review in all_reviews if review.contains_bad_words())
        self.assertEqual(offensive_count, 1)
        
        # Test admin actions
        from .views import AdminReviewActionView
        action_view = AdminReviewActionView()
        action_view.request = type('Request', (), {'user': self.admin_user})()
        
        # Approve unapproved review
        unapproved_review = reviews[0]
        unapproved_review.is_visible = True
        unapproved_review.save()
        
        # Verify notification was created
        notification = Notification.objects.filter(user=unapproved_review.user).first()
        self.assertIsNotNone(notification)
        
        # Verify admin report creation
        admin_report = AdminReport.objects.create(
            review=reviews[1],
            status='rejected'
        )
        self.assertEqual(admin_report.status, 'rejected')

