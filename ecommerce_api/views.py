from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db.models import Q
import json
import random
import string
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from .models import (
    Product, UserProfile, Favorite, Cart, History,
    Review, Poster, Shipping, Order, OrderItem, Otp
)
from .serializers import (
    UserSerializer, ProductSerializer, FavoriteSerializer,
    HistorySerializer, ReviewSerializer, PosterSerializer, ShippingSerializer,
    OrderSerializer, OtpSerializer
)


# Pagination pour les produits
class ProductPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


# Authentification
@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        response_data = {
            'success': True,
            'message': 'Utilisateur créé avec succès',
            'user_id': user.pk,
            'email': user.email
        }
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response({
        'success': False,
        'message': 'Erreur lors de la création de l\'utilisateur',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    email = request.query_params.get('email')
    password = request.query_params.get('password')

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Email ou mot de passe incorrect'
        }, status=status.HTTP_401_UNAUTHORIZED)

    user = authenticate(username=user.username, password=password)
    if user:
        return Response({
            'success': True,
            'message': 'Connexion réussie',
            'user_id': user.pk,
            'email': user.email
        })
    else:
        return Response({
            'success': False,
            'message': 'Email ou mot de passe incorrect'
        }, status=status.HTTP_401_UNAUTHORIZED)


# OTP
@api_view(['GET'])
@permission_classes([AllowAny])
def get_otp(request):
    email = request.query_params.get('email')
    if not email:
        return Response({'error': 'Email requis'}, status=status.HTTP_400_BAD_REQUEST)

    # Générer un OTP de 6 chiffres
    otp_code = ''.join(random.choices(string.digits, k=6))

    # Enregistrer l'OTP dans la base de données
    otp, created = Otp.objects.update_or_create(
        email=email,
        defaults={'otp': otp_code}
    )

    # Envoyer l'email en production
    # send_mail(
    #     'Votre code OTP',
    #     f'Votre code de vérification est : {otp_code}',
    #     'from@example.com',
    #     [email],
    #     fail_silently=False,
    # )

    # Pour le développement, retourner l'OTP
    serializer = OtpSerializer(otp)
    return Response(serializer.data)


# Fonctions pour utilisateurs
@api_view(['DELETE'])
def delete_account(request, userId):
    user = get_object_or_404(User, id=userId)
    user.delete()
    return Response(status=status.HTTP_200_OK)


@api_view(['PUT'])
@parser_classes([MultiPartParser, FormParser])
def upload_photo(request):
    user_id = request.data.get('id')
    user_photo = request.data.get('userPhoto')

    user = get_object_or_404(User, id=user_id)
    profile, created = UserProfile.objects.get_or_create(user=user)

    if profile.photo:
        if default_storage.exists(profile.photo.name):
            default_storage.delete(profile.photo.name)

    profile.photo = user_photo
    profile.save()

    return Response(status=status.HTTP_200_OK)


@api_view(['PUT'])
def update_password(request):
    password = request.query_params.get('password')
    user_id = request.query_params.get('id')

    user = get_object_or_404(User, id=user_id)
    user.set_password(password)
    user.save()

    return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
def get_user_image(request):
    user_id = request.query_params.get('id')
    user = get_object_or_404(User, id=user_id)

    try:
        profile = UserProfile.objects.get(user=user)
        if profile.photo:
            return HttpResponse(profile.photo, content_type="image/jpeg")
    except UserProfile.DoesNotExist:
        pass

    return Response({"error": "No image found"}, status=status.HTTP_404_NOT_FOUND)


# Fonctions pour produits
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def insert_product(request):
    product_info = {}
    for key, value in request.data.items():
        if key != 'image':
            product_info[key] = value

    product = Product.objects.create(
        product_name=product_info.get('product_name'),
        price=product_info.get('price'),
        quantity=product_info.get('quantity', 0),
        supplier=product_info.get('supplier', ''),
        category=product_info.get('category', ''),
        image=request.data.get('image')
    )

    return Response(status=status.HTTP_201_CREATED)


@api_view(['GET'])
def get_products(request):
    paginator = ProductPagination()
    page = request.query_params.get('page', 1)

    products = Product.objects.all()
    result_page = paginator.paginate_queryset(products, request)

    serializer = ProductSerializer(result_page, many=True)
    return Response({"products": serializer.data})


@api_view(['GET'])
def get_products_by_category(request):
    paginator = ProductPagination()
    category = request.query_params.get('category')
    user_id = request.query_params.get('userId')
    page = request.query_params.get('page', 1)

    products = Product.objects.filter(category=category)
    result_page = paginator.paginate_queryset(products, request)

    serializer = ProductSerializer(result_page, many=True, context={'user_id': user_id})
    return Response({"products": serializer.data})


@api_view(['GET'])
def search_for_product(request):
    keyword = request.query_params.get('q', '')
    user_id = request.query_params.get('userId')

    products = Product.objects.filter(
        Q(product_name__icontains=keyword) |
        Q(supplier__icontains=keyword) |
        Q(category__icontains=keyword)
    )

    serializer = ProductSerializer(products, many=True, context={'user_id': user_id})
    return Response({"products": serializer.data})


# Fonctions pour favoris
@api_view(['POST'])
@parser_classes([JSONParser])
def add_favorite(request):
    serializer = FavoriteSerializer(data=request.data)
    if serializer.is_valid():
        # Vérifier si le favori existe déjà
        user_id = serializer.validated_data['userId']
        product_id = serializer.validated_data['productId']

        favorite, created = Favorite.objects.get_or_create(
            userId=user_id,
            productId=product_id
        )

        return Response(status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def remove_favorite(request):
    user_id = request.query_params.get('userId')
    product_id = request.query_params.get('productId')

    favorite = get_object_or_404(Favorite, userId=user_id, productId=product_id)
    favorite.delete()

    return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
def get_favorites(request):
    user_id = request.query_params.get('userId')

    # Récupérer tous les IDs de produits favoris pour cet utilisateur
    favorite_ids = Favorite.objects.filter(userId=user_id).values_list('productId', flat=True)

    # Récupérer tous les produits correspondant à ces IDs
    products = Product.objects.filter(id__in=favorite_ids)

    serializer = ProductSerializer(products, many=True, context={'user_id': user_id})
    return Response({"favorites": serializer.data})


# Fonctions pour panier
@api_view(['POST'])
@parser_classes([JSONParser])
def add_to_cart(request):
    try:
        cart_data = request.data.get('cart')

        # Créer un objet Cart avec la chaîne JSON
        cart = Cart(cart=cart_data)

        # Extraire les informations de la chaîne JSON pour les champs supplémentaires
        cart_json = json.loads(cart_data)
        cart.userId = cart_json.get('userId')
        cart.productId = cart_json.get('productId')
        cart.quantity = cart_json.get('quantity', 1)

        # Vérifier si le produit existe déjà dans le panier
        existing_cart = Cart.objects.filter(userId=cart.userId, productId=cart.productId).first()
        if existing_cart:
            existing_cart.quantity = cart.quantity
            existing_cart.cart = cart_data
            existing_cart.save()
        else:
            cart.save()

        return Response(status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def remove_from_cart(request):
    user_id = request.query_params.get('userId')
    product_id = request.query_params.get('productId')

    cart = get_object_or_404(Cart, userId=user_id, productId=product_id)
    cart.delete()

    return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
def get_products_in_cart(request):
    user_id = request.query_params.get('userId')

    # Récupérer tous les IDs de produits dans le panier pour cet utilisateur
    cart_items = Cart.objects.filter(userId=user_id)
    cart_product_ids = cart_items.values_list('productId', flat=True)

    # Récupérer tous les produits correspondant à ces IDs
    products = Product.objects.filter(id__in=cart_product_ids)

    serializer = ProductSerializer(products, many=True, context={'user_id': user_id})
    return Response({"carts": serializer.data})


# Fonctions pour l'historique
@api_view(['POST'])
def add_to_history(request):
    serializer = HistorySerializer(data=request.data)
    if serializer.is_valid():
        # Mettre à jour l'horodatage ou créer une nouvelle entrée
        history, created = History.objects.update_or_create(
            userId=serializer.validated_data['userId'],
            productId=serializer.validated_data['productId'],
            defaults={'viewed_at': timezone.now()}
        )

        return Response(status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def remove_all_from_history(request):
    History.objects.all().delete()
    return Response(status=status.HTTP_200_OK)


@api_view(['GET'])
def get_products_in_history(request):
    user_id = request.query_params.get('userId')
    page = request.query_params.get('page', 1)

    paginator = ProductPagination()

    # Récupérer les IDs des produits dans l'historique
    history_items = History.objects.filter(userId=user_id).order_by('-viewed_at')
    history_product_ids = history_items.values_list('productId', flat=True)

    # Récupérer les produits correspondants
    # Préserver l'ordre de l'historique
    products_dict = {p.id: p for p in Product.objects.filter(id__in=history_product_ids)}
    products = [products_dict.get(pid) for pid in history_product_ids if pid in products_dict]

    result_page = paginator.paginate_queryset(products, request)

    serializer = ProductSerializer(result_page, many=True, context={'user_id': user_id})
    return Response({"history": serializer.data})


# Fonctions pour les avis
@api_view(['POST'])
def add_review(request):
    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_all_reviews(request):
    product_id = request.query_params.get('productId')

    reviews = Review.objects.filter(productId=product_id).order_by('-created_at')

    serializer = ReviewSerializer(reviews, many=True)
    return Response({"reviews": serializer.data})


# Fonction pour les posters (bannières)
@api_view(['GET'])
def get_posters(request):
    posters = Poster.objects.all().order_by('-date_added')

    serializer = PosterSerializer(posters, many=True)
    return Response({"posters": serializer.data})


# Fonctions pour les commandes
@api_view(['GET'])
def get_orders(request):
    user_id = request.query_params.get('userId')

    orders = Order.objects.filter(userId=user_id).order_by('-created_at')

    serializer = OrderSerializer(orders, many=True)
    return Response({"orders": serializer.data})


@api_view(['POST'])
def add_shipping_address(request):
    serializer = ShippingSerializer(data=request.data)
    if serializer.is_valid():
        shipping = serializer.save()
        return Response(status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def order_product(request):
    try:
        data = request.data

        # Créer la commande
        order = Order.objects.create(
            userId=data.get('userId'),
            shippingId=data.get('shippingId'),
            payment_method=data.get('paymentMethod', 'card'),
            total_price=data.get('totalPrice', 0)
        )

        # Ajouter les produits commandés
        products = data.get('products', [])
        for product_data in products:
            OrderItem.objects.create(
                order=order,
                productId=product_data.get('productId'),
                quantity=product_data.get('quantity', 1),
                price=product_data.get('price', 0)
            )

            # Supprimer le produit du panier
            Cart.objects.filter(
                userId=data.get('userId'),
                productId=product_data.get('productId')
            ).delete()

        return Response(status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
