from django.urls import path
from . import views

urlpatterns = [
    # Authentification
    path('users/register', views.register_user, name='register'),
    path('users/login', views.login_user, name='login'),
    path('users/otp', views.get_otp, name='get_otp'),

    # Utilisateurs
    path('users/<int:userId>', views.delete_account, name='delete_account'),
    path('users/upload', views.upload_photo, name='upload_photo'),
    path('users/info', views.update_password, name='update_password'),
    path('users/getImage', views.get_user_image, name='get_user_image'),

    # Produits
    path('products/insert', views.insert_product, name='insert_product'),
    path('products', views.get_products, name='get_products'),
    path('products/search', views.search_for_product, name='search_for_product'),

    # Favoris
    path('favorites/add', views.add_favorite, name='add_favorite'),
    path('favorites/remove', views.remove_favorite, name='remove_favorite'),
    path('favorites', views.get_favorites, name='get_favorites'),

    # Panier
    path('carts/add', views.add_to_cart, name='add_to_cart'),
    path('carts/remove', views.remove_from_cart, name='remove_from_cart'),
    path('carts', views.get_products_in_cart, name='get_products_in_cart'),

    # Historique
    path('history/add', views.add_to_history, name='add_to_history'),
    path('history/remove', views.remove_all_from_history, name='remove_all_from_history'),
    path('history', views.get_products_in_history, name='get_products_in_history'),

    # Avis
    path('review/add', views.add_review, name='add_review'),
    path('review', views.get_all_reviews, name='get_all_reviews'),

    # Posters
    path('posters', views.get_posters, name='get_posters'),

    # Commandes
    path('orders/get', views.get_orders, name='get_orders'),
    path('address/add', views.add_shipping_address, name='add_shipping_address'),
    path('orders/add', views.order_product, name='order_product'),
]
