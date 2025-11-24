"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Ruta raíz (Home)
    path('', views.home, name='home'),
    
    # Rutas de autenticación
    path('registro/', views.registro, name='registro'),
    path('login/', views.login_custom, name='login'),
    path('onboarding/', views.cuestionario_estilo, name='cuestionario'),
    path('home', views.home, name= 'home'),
    path('crear_pedido/', views.crear_pedido, name='crear_pedido'),
    path('mi-caja/', views.ver_pedido, name='ver_pedido'),
    path('generando-pedido/', views.generando_pedido, name='generando_pedido'), 
    path('perfil/', views.ver_perfil, name='ver_perfil'),
    path('historial/', views.historial_pedidos, name='historial'),
    path('pedido/<int:pedido_id>/', views.detalle_pedido, name='detalle_pedido'),
    path('devolucion/<int:pedido_id>/', views.gestionar_devolucion, name='gestionar_devolucion'),
    path('procesar-pago/<int:pedido_id>/', views.procesar_pago, name='procesar_pago'),
    
]