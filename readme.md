# Product Reviews & Ratings API
نظام تقييم ومراجعات المنتجات (Product Reviews & Ratings System)
نظام REST API مبني باستخدام Django وDjango REST Framework (DRF) ، يسمح للمستخدمين بإضافة مراجعات وتقييمات للمنتجات، ويتيح للمشرفين الموافقة عليها.

🔧 الميزات الرئيسية
✨ تسجيل المستخدم وتسجيل الدخول باستخدام JWT Authentication
✅ إنشاء منتجات جديدة
💬 كتابة مراجعات وتقييم النجوم (1-5)
👮‍♂️ صلاحيات واضحة:
المستخدمون يمكنهم تعديل/حذف مراجعاتهم فقط.
المشرفون فقط يمكنهم الموافقة على المراجعات.
🔍 فلاتر متقدمة: البحث حسب المنتج أو التقييم
📊 عرض متوسط التقييم وعدد المراجعات لكل منتج
🧪 اختبارات وحدوية كاملة
📦 Postman Collection جاهز لتجربة الـ API

🧩 المتطلبات التقنية
Python >= 3.8
اللغة الأساسية للمشروع
Django
إطار العمل الأساسي
DRF (Django REST Framework)
بناء الـ API
djangorestframework-simplejwt
دعم توكنات JWT
django-filter
الفلاتر في الـ API

## 📖 Overview
A REST API for managing product reviews and ratings, allowing users to create reviews, and administrators to approve them.
##  - Admin Insights System :

### نظام تقارير المشرف الذكي
تم تطوير نظام شامل لتحليل وإدارة مراجعات المنتجات من منظور المشرف:



#### Query Parameters للتقارير:
- `filter`: `unapproved`, `low_rated`, `offensive`, `all`
- `product_id`: تصفية حسب منتج معين
- `rating`: تصفية حسب التقييم
- `date_from` & `date_to`: تصفية حسب التاريخ

---

## 🚀 Features
- JWT Authentication
- CRUD Operations for Reviews
- Filter reviews by product and rating
- Average rating and count of approved reviews
- Admin-only review approval
- **NEW**: Comprehensive Admin Insights System
- **NEW**: Smart Review Management
- **NEW**: Offensive Content Detection
- **NEW**: Interactive Admin Dashboard
- **NEW for task 9**: Added a counter to track the number of reviews each user has submitted.
#### الميزات الجديدة:
- 📊 **تقارير شاملة**: إحصائيات المراجعات غير الموافق عليها، منخفضة التقييم، والمحتوى المسيء
- 🎛️ **إدارة المراجعات**: موافقة، رفض، وإشارة المراجعات
- 📈 **لوحة تحكم تفاعلية**: إحصائيات مفصلة وتوزيع التقييمات
- 🚨 **كشف المحتوى المسيء**: فحص تلقائي للمراجعات المسيئة
- 🔔 **نظام إشعارات**: إشعارات تلقائية للمستخدمين
-  **عداد المشاهدات للتاسك 9**: تم إضافة عداد لتتبع عدد المراجعات التي يقدمها كل مستخدم
## 🛠️ Installation
1. Clone the repository:
   ```bash
   git clone <https://github.com/rahafha1/product_review_system>
   cd product_review_system
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```bash
   python manage.py migrate
   ```

4. Create superuser:
   ```bash
   python manage.py createsuperuser
   ```

5. Run the server:
   ```bash
   python manage.py runserver
   ```

## 📚 API Endpoints

### Authentication
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/register/` | POST | User registration |
| `/api/token/` | POST | User login (JWT) |
| `/api/token/refresh/` | POST | Refresh JWT token |
| `/logout/` | POST | User logout |

### Products & Reviews
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/products/` | GET/POST | List/Create products |
| `/products/<id>/` | GET/PUT/DELETE | Product details |
| `/products/<product_id>/reviews/` | GET/POST | List/Create reviews |
| `/products/<product_id>/ratings/` | GET | Get product rating info |
| `/products/<product_id>/top-review/` | GET | Get top review for product |

### Admin Insights System (NEW)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/reports/` | GET | Comprehensive admin reports |
| `/admin/reviews/{id}/approve/` | POST | Approve review |
| `/admin/reviews/{id}/reject/` | POST | Reject review |
| `/admin/reviews/{id}/flag/` | POST | Flag review for review |
| `/admin/dashboard/` | GET | Interactive admin dashboard |
#### Endpoints الجديدة:
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/reports/` | GET | تقارير المشرف الشاملة |
| `/admin/reviews/{id}/approve/` | POST | الموافقة على مراجعة |
| `/admin/reviews/{id}/reject/` | POST | رفض مراجعة |
| `/admin/reviews/{id}/flag/` | POST | إشارة مراجعة |
| `/admin/dashboard/` | GET | لوحة التحكم التفاعلية |


### Review Interactions
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/review-interactions/` | GET/POST | Review interactions (like/helpful) |
| `/review-interactions/review/{id}/stats/` | GET | Review interaction statistics |

## 🔧 Usage Examples

### Admin Reports
```bash
# Get all admin reports
GET /admin/reports/

# Filter unapproved reviews
GET /admin/reports/?filter=unapproved

# Filter low-rated reviews
GET /admin/reports/?filter=low_rated

# Filter offensive content
GET /admin/reports/?filter=offensive

# Filter by product
GET /admin/reports/?product_id=1

# Filter by date range
GET /admin/reports/?date_from=2024-01-01&date_to=2024-12-31
```

### Review Management
```bash
# Approve a review
POST /admin/reviews/123/approve/

# Reject a review
POST /admin/reviews/123/reject/

# Flag a review
POST /admin/reviews/123/flag/
```

### Admin Dashboard
```bash
# Get comprehensive dashboard
GET /admin/dashboard/
```

## 🧪 Testing
Run the test suite:
```bash
python manage.py test
```

The test suite includes:
- Authentication tests
- Product and review CRUD tests
- Admin insights system tests
- Review interaction tests
- Integration tests

## 📦 Postman Collection
Import the provided Postman collection (`admin_insights_postman_collection.json`) to test all endpoints including the new Admin Insights System.

## 🔒 Security Features
- JWT Authentication
- Role-based permissions
- Product owner authorization
- Input validation
- Offensive content detection

## 📊 Admin Insights Features
- **Comprehensive Reporting**: Unapproved, low-rated, and offensive reviews
- **Smart Filtering**: Multiple filter options for detailed analysis
- **Review Management**: Approve, reject, and flag reviews
- **Interactive Dashboard**: Statistics, charts, and alerts
- **Notification System**: Automatic user notifications
- **Offensive Content Detection**: Automatic bad word filtering

## 🚀 Future Enhancements
- Sentiment Analysis integration
- Data export to CSV/Excel
- Advanced analytics and trends
- Real-time notifications
- Email notifications

---


## 📝 Documentation
For detailed documentation about the Admin Insights System, see `admin_insights_documentation.md`.

## 👥 Team Task Distribution
| Task | Description | Status |
|------|-------------|--------|
| 1 | Analytics System | Pending |
| 2 | Review Interactions | Completed |
| 3 | Notifications System | Pending |
| 4 | **Admin Insights System** | **✅ Completed** |

## 📞 Support
For questions or issues, please refer to the documentation or create an issue in the repository.

# newwwwwwwwwwwwwww ######
# new update ( review details & comments on reviews & admin permissions & new tests && updated urls )

## 🧠 Review Detail & Comments Enhancements (NEW)

### عرض تفاصيل المراجعة (Review Detail View)
قمنا بتوسيع عرض تفاصيل المراجعة لتشمل التفاعلات التالية:

- `views_count`: عداد المشاهدات (يزيد تلقائيًا عند كل زيارة).
- `likes_count`: عدد الإعجابات.
- `helpful_count`: عدد التقييمات المفيدة.
- `user_liked`: حالة الإعجاب من قبل المستخدم الحالي.
- `reported`: حالة التبليغ من قبل المستخدم الحالي.
- `comments`: جميع تعليقات المراجعة المرتبطة بها.

📌 **الهدف**: تحسين تجربة عرض المراجعة من خلال جمع كافة التفاعلات في استجابة واحدة.

---

### نموذج التعليقات على المراجعة (ReviewComment Model)
أنشأنا موديل جديد لتعليقات المستخدمين على المراجعات يحتوي على:

- ارتباط بالمراجعة (`review`)
- ارتباط بالمستخدم (`user`)
- نص التعليق (`comment_text`)
- تاريخ الإنشاء (`created_at`)

✔ تم ربط التعليقات بالمراجعة باستخدام `related_name="comments"`  
✔ إنشاء Serializer: `ReviewCommentSerializer`

---

### عرض التعليقات في تفاصيل المراجعة  
تم تعديل `ReviewDetailView` لإرفاق جميع التعليقات المرتبطة بالمراجعة وترتيبها من الأحدث إلى الأقدم، وعرضها مع تفاصيل المراجعة.

---

### Endpoints جديدة لتعليقات المراجعات

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reviews/<review_id>/comments/` | GET/POST | عرض أو إضافة تعليق لمراجعة |
| `/reviews/comments/<comment_id>/` | DELETE | حذف تعليق يخص المستخدم الحالي فقط |

✔ Views:  
- `ReviewCommentListCreateView`  
- `ReviewCommentDeleteView`

---

### التحكم في صلاحيات المنتجات (Admin-only Product Management)
قمنا بتقييد صلاحيات إدارة المنتجات بحيث:

- فقط الأدمن يمكنه: الإضافة، التعديل، الحذف.
- المستخدمون الآخرون يمكنهم فقط **قراءة** المنتجات.

> استخدمنا `IsAdminUser` من Django REST Framework دون الحاجة لتعديل `permissions.py`.

✔ تم إنشاء الأدمن باستخدام:
```bash
python manage.py createsuperuser

## 🧠 Review Detail & Comments Enhancements (NEW)

### Review Detail View Improvements
We expanded the review detail view to include the following interactions:

- `views_count`: Number of views (automatically increments on each request).
- `likes_count`: Number of likes.
- `helpful_count`: Number of helpful ratings.
- `user_liked`: Whether the current user liked the review.
- `reported`: Whether the current user reported the review.
- `comments`: List of all comments related to the review.

📌 **Purpose**: Enhance the review display experience by consolidating all interactions in a single response.

---

### ReviewComment Model
We created a new model for user comments on reviews, containing:

- ForeignKey to the review (`review`)
- ForeignKey to the user (`user`)
- Comment text (`comment_text`)
- Creation timestamp (`created_at`)

✔ Linked comments to Review model using `related_name="comments"`  
✔ Created `ReviewCommentSerializer`

---

### Displaying Comments in Review Detail
Modified `ReviewDetailView` to include all related comments ordered from newest to oldest alongside the review details.

---

### New API Endpoints for Review Comments

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/reviews/<review_id>/comments/` | GET/POST | List or add comments for a review |
| `/reviews/comments/<comment_id>/` | DELETE | Delete a comment owned by the current user |

✔ Views added:  
- `ReviewCommentListCreateView`  
- `ReviewCommentDeleteView`

---

### Product Management Permissions (Admin Only)
Restricted product management permissions so that:

- Only admins can create, update, or delete products.
- Other users have read-only access.

> Utilized DRF’s built-in `IsAdminUser` permission without modifying `permissions.py`.

✔ Created admin user with:
```bash
python manage.py createsuperuser



## ✅ Unit Tests Summary

This project includes comprehensive test coverage for the product review system. The main test cases are as follows:

### 🔐 Authentication & Registration

- **Register New User**: Verifies user registration and JWT token generation.

### ✍️ Product Reviews

- **Prevent Editing Others' Reviews**: Ensures users cannot edit reviews they don't own.
- **Admin Approval of Reviews**: Confirms admin can approve hidden reviews and make them visible.
- **Product Rating Info**: Calculates the average rating and number of approved reviews accurately.

### 🤝 Review Interactions

- **Disallow Self-Interaction**: Prevents users from interacting with their own reviews.
- **Interact with Others' Reviews**: Allows liking/helping others’ reviews.
- **Prevent Duplicate Interactions**: Enforces one interaction per user per review.
- **Update Interaction**: Tests editing an existing interaction.
- **Delete Interaction**: Ensures a user can delete their interaction.
- **Review Stats**: Fetches interaction statistics (likes and helpful votes) per review.

### 🌟 Product Analytics

- **Top Review**: Identifies the most engaged review on a product based on interactions.

All test cases were executed using Django’s built-in `TestCase` framework and `APIClient` from DRF.


## 🔌 API Endpoints for the final project 

### ✅ Authentication
- `POST /api/register/` → Register a new user
- `POST /api/token/` → Get JWT token (login)
- `POST /api/token/refresh/` → Refresh JWT token
- `POST /api/logout/` → Logout the user

---

### 📦 Products
- `GET /api/products/` → List all products
- `POST /api/products/` → Create a new product
- `GET /api/products/{id}/` → Retrieve a product
- `PUT /api/products/{id}/` → Update a product
- `DELETE /api/products/{id}/` → Delete a product
- `GET /api/products/{id}/ratings/` → Get product rating stats
- `GET /api/products/{id}/top-review/` → Get top review for a product

---

### 📝 Reviews
- `GET /api/products/{product_id}/reviews/` → List reviews for a product
- `POST /api/products/{product_id}/reviews/` → Add a review to a product
- `GET /api/products/{product_id}/reviews/{review_id}/` → Review detail by product
- `GET /api/reviews/{review_id}/` → Review detail directly
- `PUT /api/reviews/{review_id}/` → Update a review
- `DELETE /api/reviews/{review_id}/` → Delete a review
- `POST /api/reviews/{review_id}/comment/` → Add comment to a review

---

### 💬 Review Comments
- `GET /api/review-comments/` → List all review comments
- `POST /api/review-comments/` → Add a new comment
- `GET /api/review-comments/{id}/` → Retrieve a comment
- `PUT /api/review-comments/{id}/` → Update a comment
- `DELETE /api/review-comments/{id}/` → Delete a comment

---

### ❤️ Review Interactions
- `GET /api/review-interactions/` → List all interactions for
