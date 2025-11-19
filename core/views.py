# core/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Users, StyleProfiles
from .forms import LoginForm, RegistroForm

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
            # 1. Guardar el usuario sin commit para modificar campos
            nuevo_usuario = form.save(commit=False)
            nuevo_usuario.hashed_password = form.cleaned_data['password'] 
            nuevo_usuario.rol = 'CLIENTE' 
            nuevo_usuario.personal_shopper_id = 1 
            nuevo_usuario.save()

            # 2. Crear perfil de estilo
            StyleProfiles.objects.create(client_id=nuevo_usuario.id)

            messages.success(request, "¡Cuenta creada! Ahora inicia sesión.")
            return redirect('login')
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