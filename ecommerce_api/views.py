from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status, generics
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
    Review, Poster, Shipping, Order, OrderItem, Otp, Notification
)
from .serializers import (
    UserSerializer, ProductSerializer, FavoriteSerializer,
    HistorySerializer, ReviewSerializer, PosterSerializer, ShippingSerializer,
    OrderSerializer, OtpSerializer, NotificationListSerializer
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


@api_view(['GET'])
def get_user_details(request, userId):
    """
    Récupère les informations détaillées d'un utilisateur spécifique.

    Args:
        request: La requête HTTP
        userId: L'ID de l'utilisateur à récupérer

    Returns:
        Les informations complètes de l'utilisateur au format JSON
    """
    try:
        user = get_object_or_404(User, id=userId)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erreur lors de la récupération des données utilisateur: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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


@api_view(['PUT'])
def update_profile(request):
    """
    Endpoint pour mettre à jour le nom d'utilisateur et l'email d'un utilisateur
    """
    username = request.query_params.get('username')
    email = request.query_params.get('email')
    user_id = request.query_params.get('id')

    # Validation des paramètres
    if not all([username, email, user_id]):
        return Response({"error": "Tous les paramètres sont requis"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = get_object_or_404(User, id=user_id)

        # Vérification si l'email existe déjà pour un autre utilisateur
        if User.objects.filter(email=email).exclude(id=user_id).exists():
            return Response({"error": "Cette adresse email est déjà utilisée"}, status=status.HTTP_400_BAD_REQUEST)

        # Mise à jour des informations
        user.username = username
        user.email = email
        user.save()

        return Response(status=status.HTTP_200_OK)

    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
def get_all_products(request):
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
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
        user_id = serializer.validated_data['userId']
        product_id = serializer.validated_data['productId']

        favorite, created = Favorite.objects.get_or_create(
            userId=user_id,
            productId=product_id
        )

        if created:
            user = User.objects.get(id=user_id)
            product = Product.objects.get(id=product_id)
            Notification.objects.create(
                user=user,
                title="Produit ajouté à vos favoris",
                message=f"Le produit '{product.product_name}' a été ajouté à vos favoris.",
                type="general",
                data={"product_id": product_id}
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
        # The request.data already contains the cart information directly
        cart_data = request.data

        # Extract the information directly from request.data
        user_id = cart_data.get('userId')
        product_id = cart_data.get('productId')
        quantity = cart_data.get('quantity', 1)

        # Validate required fields
        if not user_id or not product_id:
            return Response({'error': 'userId and productId are required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the product already exists in the cart
        existing_cart = Cart.objects.filter(userId=user_id, productId=product_id).first()

        if existing_cart:
            # Update existing cart item
            existing_cart.quantity = quantity
            existing_cart.cart = json.dumps(cart_data)  # Store as JSON string if needed
            existing_cart.save()
        else:
            # Create new cart item
            cart = Cart(
                userId=user_id,
                productId=product_id,
                quantity=quantity,
                cart=json.dumps(cart_data)  # Store as JSON string if needed
            )
            cart.save()

        return Response({'message': 'Item added to cart successfully'}, status=status.HTTP_200_OK)

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
        review = serializer.save()

        user = User.objects.get(id=review.userId)
        product = Product.objects.get(id=review.productId)

        Notification.objects.create(
            user=user,
            title="Avis publié",
            message=f"Votre avis sur le produit '{product.product_name}' a été publié.",
            type="general",
            data={"product_id": product.id}
        )

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

        user = User.objects.get(id=shipping.userId)
        Notification.objects.create(
            user=user,
            title="Nouvelle adresse ajoutée",
            message="Votre nouvelle adresse de livraison a été enregistrée.",
            type="account",
            data={"address_id": shipping.id}
        )

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

        user = User.objects.get(id=data.get('userId'))
        Notification.objects.create(
            user=user,
            title="Nouvelle commande passée",
            message=f"Votre commande #{order.id} a été créée avec succès.",
            type="order",
            data={
                "order_id": order.id,
                "total": float(order.total_price),
                "status": order.status
            }
        )

        return Response(status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationListSerializer
    #permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        user_id = (request.GET.get('userId'))
        page = int(request.GET.get('page', 1))
        per_page = 20

        try:
            user = User.objects.get(id=user_id)

            # Récupérer toutes les notifications de l'utilisateur
            notifications = Notification.objects.filter(user=user)

            # Compter les notifications non lues
            unread_count = notifications.filter(is_read=False).count()
            total_count = notifications.count()

            # Pagination
            paginator = Paginator(notifications, per_page)
            notifications_page = paginator.get_page(page)

            # Sérialiser les données
            serializer = self.get_serializer(notifications_page, many=True)

            return Response({
                'success': True,
                'message': 'Notifications récupérées avec succès',
                'notifications': serializer.data,
                'total_pages': paginator.num_pages,
                'current_page': page,
                'total_count': total_count,
                'unread_count': unread_count
            })
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Accès non autorisé'
            }, status=status.HTTP_403_FORBIDDEN)


@api_view(['PUT'])
#@permission_classes([IsAuthenticated])
def mark_notification_as_read(request, notificationId):
    try:
        notification = get_object_or_404(Notification, id=notificationId, user=request.user)
        notification.is_read = True
        notification.save()

        return Response({
            'success': True,
            'message': 'Notification marquée comme lue'
        })

    except Notification.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Notification non trouvée'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
#@permission_classes([IsAuthenticated])
def delete_notification(request, notificationId):
    try:
        notification = get_object_or_404(Notification, id=notificationId, user=request.user)
        notification.delete()

        return Response({
            'success': True,
            'message': 'Notification supprimée'
        })

    except Notification.DoesNotExist:
        return Response({
            'success': False,
            'message': 'Notification non trouvée'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
#@permission_classes([IsAuthenticated])
def mark_all_as_read(request):
    try:
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        notifications.update(is_read=True)

        return Response({
            'success': True,
            'message': f'{notifications.count()} notifications marquées comme lues'
        })

    except Exception as e:
        return Response({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
