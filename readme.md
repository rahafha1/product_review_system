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

## 🚀 Features
- JWT Authentication
- CRUD Operations for Reviews
- Filter reviews by product and rating
- Average rating and count of approved reviews
- Admin-only review approval

## 🛠️ Installation
1. Clone the repository:
   ```bash
   git clone <https://github.com/rahafha1/product_review_system>
| Endpoint                              | Method | Description                     |
| ------------------------------------- | ------ | ------------------------------- |
| `/register/`                          | POST   | User registration               |
| `/logout/`                            | POST   | User logout                     |
| `/products/<product_id>/reviews/`     | GET    | List/Create reviews for product |
| `/products/<product_id>/ratings/`     | GET    | Get product rating info         |
| `/admin/reviews/<review_id>/approve/` | POST   | Approve a review (admin only)   |


---


