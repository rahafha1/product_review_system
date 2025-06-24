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
   git clone <repository_url>
| Endpoint                              | Method | Description                     |
| ------------------------------------- | ------ | ------------------------------- |
| `/register/`                          | POST   | User registration               |
| `/logout/`                            | POST   | User logout                     |
| `/products/<product_id>/reviews/`     | GET    | List/Create reviews for product |
| `/products/<product_id>/ratings/`     | GET    | Get product rating info         |
| `/admin/reviews/<review_id>/approve/` | POST   | Approve a review (admin only)   |


---

### **5. ملف Postman:**

إنشاء ملف Postman يتضمن:
1. تسجيل المستخدم.
2. تسجيل الدخول والحصول على توكن.
3. إنشاء مراجعة.
4. الموافقة على مراجعة من قبل المشرف.
5. عرض المراجعات وتصفيتها.

---

### **6. عمل Pull Request:**
بعد كتابة README ورفع المشروع على GitHub، افتحي Pull Request، وتحققي من التعديلات قبل الدمج مع الفرع الأساسي.
postman

https://documenter.getpostman.com/view/41721476/2sB2xBEAat