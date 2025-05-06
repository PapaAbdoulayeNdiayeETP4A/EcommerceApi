from django.db import models
from django.contrib.auth.models import User


class Product(models.Model):
    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    supplier = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    image = models.ImageField(upload_to='products/')

    def __str__(self):
        return self.product_name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    photo = models.ImageField(upload_to='users/', null=True, blank=True)

    def __str__(self):
        return self.user.username


class Favorite(models.Model):
    userId = models.IntegerField()
    productId = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('userId', 'productId')

    def __str__(self):
        return f"User {self.userId} - Product {self.productId}"


class Cart(models.Model):
    cart = models.TextField()  # JSON string, comme dans votre Cart.java
    userId = models.IntegerField()
    productId = models.IntegerField()
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('userId', 'productId')

    def __str__(self):
        return f"User {self.userId} - Product {self.productId} ({self.quantity})"


# Modèles pour les fonctionnalités commentées
class History(models.Model):
    userId = models.IntegerField()
    productId = models.IntegerField()
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('userId', 'productId')
        ordering = ['-viewed_at']

    def __str__(self):
        return f"User {self.userId} - Product {self.productId}"


class Review(models.Model):
    userId = models.IntegerField()
    productId = models.IntegerField()
    rating = models.IntegerField(default=5)
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by User {self.userId} on Product {self.productId}"


class Poster(models.Model):
    title = models.CharField(max_length=255)
    image = models.ImageField(upload_to='posters/')
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Shipping(models.Model):
    userId = models.IntegerField()
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)

    def __str__(self):
        return f"Address for {self.name} (User {self.userId})"


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    )

    userId = models.IntegerField()
    shippingId = models.IntegerField()
    payment_method = models.CharField(max_length=50)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by User {self.userId}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    productId = models.IntegerField()
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"OrderItem {self.id} - Product {self.productId}"


class Otp(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.email}"
