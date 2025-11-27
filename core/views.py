# core/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Users, StyleProfiles
from .forms import LoginForm, RegistroForm
from .forms import PerfilEstiloForm
from django.shortcuts import get_object_or_404

# --- VISTA DE INICIO (Donde vas después de loguearte) ---
def home(request):
    # Recuperamos el nombre de la sesión si existe
    usuario_nombre = request.session.get('usuario_nombre', 'Invitado')
    return render(request, 'core/home.html', {'nombre': usuario_nombre})

# --- VISTA DE REGISTRO ---
def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            # 1. Guardar el usuario
            nuevo_usuario = form.save(commit=False)
            nuevo_usuario.hashed_password = form.cleaned_data['password'] 
            nuevo_usuario.rol = 'CLIENTE' 
            nuevo_usuario.personal_shopper_id = 1 
            nuevo_usuario.save()

            # 2. Crear perfil de estilo
            StyleProfiles.objects.create(client_id=nuevo_usuario.id)

            # --- CAMBIO CLAVE: AUTO-LOGIN ---
            # En lugar de mandarlo al login, iniciamos la sesión aquí mismo
            request.session['usuario_id'] = nuevo_usuario.id
            request.session['usuario_nombre'] = nuevo_usuario.nombre

            # Mensaje de éxito
            messages.success(request, "¡Bienvenido/a! Antes de empezar, Asterion necesita conocerte.")
            
            # --- REDIRECCIÓN DIRECTA AL ONBOARDING ---
            return redirect('cuestionario') 

    else:
        form = RegistroForm()

    return render(request, 'core/registro.html', {'form': form})

# --- VISTA DE LOGIN ---
def login_custom(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']

            try:
                usuario = Users.objects.get(email=email)
                
                if usuario.hashed_password == password:
                    # Guardar sesión
                    request.session['usuario_id'] = usuario.id
                    request.session['usuario_nombre'] = usuario.nombre

                    # REDIRECCIÓN CAMBIADA: Ahora va a 'home' en vez de 'catalogo'
                    return redirect('home') 
                else:
                    messages.error(request, "Contraseña incorrecta")
            except Users.DoesNotExist:
                messages.error(request, "Este email no existe")
    else:
        form = LoginForm()

    return render(request, 'core/login.html', {'form': form})

# --- AÑADIR A core/views.py ---

from .forms import PerfilEstiloForm # <--- ¡Asegúrate de importarlo arriba!

def cuestionario_estilo(request):
    # 1. Seguridad: Verificar que el usuario está logueado
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    # 2. Obtener el perfil existente de la base de datos
    perfil = StyleProfiles.objects.get(client_id=usuario_id)

    if request.method == 'POST':
        # Cargamos el formulario con los datos enviados Y la instancia existente (UPDATE)
        form = PerfilEstiloForm(request.POST, instance=perfil)
        
        if form.is_valid():
            perfil_obj = form.save(commit=False)
            
            # OJO: El género ya viene en el form, pero el estilo complejo 
            # viene dentro de 'gustos_texto' gracias a nuestro JS.
            # Podemos guardar un resumen en 'estilo_preferido' para estadísticas.
            
            # Extraemos el estilo del texto que generó el JS (ej: "Soy Mujer. Mi estilo es Formal.")
            texto_js = form.cleaned_data['gustos_texto']
            if "Formal" in texto_js: perfil_obj.estilo_preferido = "Formal"
            elif "Casual" in texto_js: perfil_obj.estilo_preferido = "Casual"
            elif "Deportivo" in texto_js: perfil_obj.estilo_preferido = "Deportivo"
            elif "Alternativo" in texto_js: perfil_obj.estilo_preferido = "Alternativo"
            else: perfil_obj.estilo_preferido = form.cleaned_data['genero']

            perfil_obj.save()
            
            messages.success(request, "¡Análisis completado! Asterion ha definido tu estilo.")
            return redirect('home')
    else:
        # Si entra por primera vez, mostramos el formulario vacío
        form = PerfilEstiloForm(instance=perfil)

    return render(request, 'core/cuestionario.html', {'form': form})

# Añade estos imports
from django.utils import timezone
from .models import Orders, OrderItems
from .ai_logic import generar_pedido_ia




def ver_pedido(request):
    # 1. Seguridad
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    # 2. Buscar el ÚLTIMO pedido de este cliente
    # (.last() nos da el más reciente)
    ultimo_pedido = Orders.objects.filter(client_id=usuario_id).last()

    if not ultimo_pedido:
        messages.warning(request, "Aún no tienes ningún pedido. ¡Solicita uno ahora!")
        return redirect('home')

    # 3. Buscar los items (prendas) dentro de ese pedido
    # Usamos 'select_related' para traer los datos del producto (nombre, foto) de una vez
    items = OrderItems.objects.filter(order=ultimo_pedido).select_related('product')

    contexto = {
        'pedido': ultimo_pedido,
        'items': items
    }
    
    return render(request, 'core/ver_pedido.html', contexto)

# AÑADE ESTE IMPORT AL PRINCIPIO
from django.http import JsonResponse

# --- VISTA NUEVA: PÁGINA DE ESPERA ---
def generando_pedido(request):
    return render(request, 'core/generando_pedido.html')

# --- MODIFICAR: CREAR PEDIDO AHORA DEVUELVE JSON ---
def crear_pedido(request):
    # Solo usuarios logueados
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return JsonResponse({'status': 'error', 'message': 'No logueado'}, status=403)

    # 1. Llamar a la IA
    productos_seleccionados = generar_pedido_ia(usuario_id)
    
    if not productos_seleccionados:
        return JsonResponse({'status': 'error', 'message': 'Perfil incompleto'}, status=400)

    # 2. Crear el pedido
    nuevo_pedido = Orders.objects.create(
        client_id=usuario_id,
        shopper_id=1, 
        fecha_pedido=timezone.now(),
        estado='EN_PREPARACION', 
        es_primer_pedido=False, 
        coste_servicio=10.00,
        total_final=0 
    )

    # 3. Guardar items
    total_precio_ropa = 0
    for producto in productos_seleccionados:
        OrderItems.objects.create(
            order=nuevo_pedido,
            product=producto,
            se_queda_articulo=None 
        )
        total_precio_ropa += producto.precio

    nuevo_pedido.total_final = total_precio_ropa + 10
    nuevo_pedido.save()

    # CAMBIO: Devolvemos JSON en vez de redirect
    return JsonResponse({'status': 'ok', 'order_id': nuevo_pedido.id})

# --- VISTA DE PERFIL ---
def ver_perfil(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    
    # 1. Obtener datos personales
    usuario = Users.objects.get(id=usuario_id)
    
    # 2. Obtener perfil de estilo (si existe)
    try:
        perfil = StyleProfiles.objects.get(client_id=usuario_id)
    except StyleProfiles.DoesNotExist:
        perfil = None
        
    return render(request, 'core/perfil.html', {'usuario': usuario, 'perfil': perfil})


# --- HISTORIAL DE PEDIDOS (LISTA) ---
def historial_pedidos(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    # Obtenemos TODOS los pedidos del usuario, ordenados del más reciente al más antiguo
    pedidos = Orders.objects.filter(client_id=usuario_id).order_by('-fecha_pedido')

    return render(request, 'core/historial.html', {'pedidos': pedidos})

# --- DETALLE DE UN PEDIDO ESPECÍFICO ---
def detalle_pedido(request, pedido_id):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    # Buscamos el pedido por ID y nos aseguramos de que pertenece al usuario (Seguridad)
    pedido = get_object_or_404(Orders, id=pedido_id, client_id=usuario_id)
    
    # Sacamos los productos de ese pedido
    items = OrderItems.objects.filter(order=pedido).select_related('product')

    contexto = {
        'pedido': pedido,
        'items': items
    }
    # Reutilizamos la plantilla de ver_pedido o creamos una nueva si prefieres
    # Para simplificar, usaremos una nueva específica para el historial
    return render(request, 'core/detalle_pedido.html', contexto)

# core/views.py


from decimal import Decimal # Importante para cálculos de dinero

# ...

def gestionar_devolucion(request, pedido_id):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login')
        
    pedido = get_object_or_404(Orders, id=pedido_id, client_id=usuario_id)
    items = OrderItems.objects.filter(order=pedido).select_related('product')
    
    # Si es POST, procesamos el formulario
    if request.method == 'POST':
        items_quedados = 0
        total_ropa = Decimal('0.00')
        
        for item in items:
            # Leemos el radio button: "keep" o "return"
            decision = request.POST.get(f'decision_{item.id}')
            
            if decision == 'keep':
                item.se_queda_articulo = True
                item.motivo_devolucion = None
                items_quedados += 1
                total_ropa += item.product.precio
            else:
                item.se_queda_articulo = False
                # Guardamos el motivo (obligatorio según el PDF)
                item.motivo_devolucion = request.POST.get(f'motivo_{item.id}')
            
            item.save()
            
        # --- CÁLCULO FINAL (REGLAS DE NEGOCIO) ---
        precio_final = total_ropa
        
        # Regla 1: Descuento del 25% si te quedas las 5 prendas
        if items_quedados == 5:
            precio_final = precio_final * Decimal('0.75')
            
        # Regla 2: Restar los 10€ del servicio si te quedas AL MENOS UNA prenda
        # (Si devuelves todo, pierdes los 10€ que ya pagaste al principio)
        if items_quedados > 0:
            precio_final = precio_final - Decimal('10.00')
            
        # Actualizamos el pedido
        pedido.total_final = precio_final
        pedido.estado = 'ENTREGADO' # O 'DEVUELTO_PARCIAL'
        pedido.save()
        
        messages.success(request, f"Devolución gestionada. Precio final ajustado a {precio_final:.2f} €")
        
        return render(request, 'core/pago.html', {'pedido': pedido})

    return render(request, 'core/devolucion.html', {'pedido': pedido, 'items': items})

def procesar_pago(request, pedido_id):
    if request.method == 'POST':
        pedido = get_object_or_404(Orders, id=pedido_id)
        
        # Aquí iría la conexión con Stripe/PayPal real.
        # Simulamos que todo va bien:
        
        pedido.estado = 'ENTREGADO' # O 'PAGADO'
        pedido.save()
        
        messages.success(request, "¡Pago realizado correctamente! Gracias por tu compra.")
        return redirect('historial')
    
    
from django.http import JsonResponse
from .ai_logic import chat_con_asterion
import json

# --- VISTA DEL CHAT (Página) ---
def chat_view(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id: return redirect('login')
    return render(request, 'core/chat.html')

# --- API PARA ENVIAR MENSAJES (AJAX) ---
def api_chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        mensaje = data.get('mensaje', '')
        
        # Aquí podrías recuperar un historial de la BD si quisieras guardar chats
        # De momento le pasamos una lista vacía para simplificar
        respuesta_asterion = chat_con_asterion(mensaje)
        
        return JsonResponse({'respuesta': respuesta_asterion})
        
    return JsonResponse({'error': 'Método no permitido'}, status=405)