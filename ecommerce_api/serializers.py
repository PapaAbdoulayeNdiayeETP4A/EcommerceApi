from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Product, UserProfile, Favorite, Cart, History,
    Review, Poster, Shipping, Order, OrderItem, Otp
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user


class ProductSerializer(serializers.ModelSerializer):
    isFavourite = serializers.SerializerMethodField()
    isInCart = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'product_name', 'price', 'quantity', 'supplier', 'category', 'image', 'isFavourite', 'isInCart']

    def get_isFavourite(self, obj):
        user_id = self.context.get('user_id')
        if user_id:
            return 1 if Favorite.objects.filter(userId=user_id, productId=obj.id).exists() else 0
        return 0

    def get_isInCart(self, obj):
        user_id = self.context.get('user_id')
        if user_id:
            return 1 if Cart.objects.filter(userId=user_id, productId=obj.id).exists() else 0
        return 0


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ['userId', 'productId']


class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = ['cart', 'userId', 'productId', 'quantity']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['photo']


# Response serializers
class ProductApiResponse(serializers.Serializer):
    products = ProductSerializer(many=True)


class FavoriteApiResponse(serializers.Serializer):
    favorites = ProductSerializer(many=True)


class CartApiResponse(serializers.Serializer):
    carts = ProductSerializer(many=True)


# Serializers pour les modèles supplémentaires
class HistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = History
        fields = ['userId', 'productId']


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['userId', 'productId', 'rating', 'review']


class PosterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Poster
        fields = ['id', 'title', 'image']


class ShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipping
        fields = ['userId', 'name', 'address', 'city', 'country', 'postal_code', 'phone']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['productId', 'quantity', 'price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'userId', 'shippingId', 'payment_method', 'total_price', 'status', 'created_at', 'items']


class OtpSerializer(serializers.ModelSerializer):
    class Meta:
        model = Otp
        fields = ['email', 'otp']


# Serializers pour les autres réponses API
class HistoryApiResponse(serializers.Serializer):
    history = ProductSerializer(many=True)


class ReviewApiResponse(serializers.Serializer):
    reviews = ReviewSerializer(many=True)


class NewsFeedResponse(serializers.Serializer):
    posters = PosterSerializer(many=True)


class OrderApiResponse(serializers.Serializer):
    orders = OrderSerializer(many=True)


class RegisterApiResponse(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    user_id = serializers.IntegerField(required=False)
    email = serializers.EmailField(required=False)


class LoginApiResponse(serializers.Serializer):
    success = serializers.BooleanField()
    message = serializers.CharField()
    user_id = serializers.IntegerField(required=False)
    email = serializers.EmailField(required=False)
