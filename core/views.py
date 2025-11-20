# core/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Users, StyleProfiles
from .forms import LoginForm, RegistroForm
from .forms import PerfilEstiloForm

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

