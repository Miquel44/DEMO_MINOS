# core/ai_logic.py
import google.generativeai as genai
import os
import json
import random
from dotenv import load_dotenv
from django.db.models import Q # Importante para consultas complejas (OR/AND)
from .models import Products, StyleProfiles

# Cargar claves
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def generar_pedido_ia(cliente_id):
    """
    1. Lee el perfil del cliente.
    2. FILTRA productos en la BD (por género/sección).
    3. Pregunta a Gemini cuáles elegir de esa selección reducida.
    4. Devuelve una lista de 5 objetos Product.
    """
    
    # 1. Obtener datos del cliente
    try:
        perfil = StyleProfiles.objects.get(client_id=cliente_id)
    except StyleProfiles.DoesNotExist:
        return []

    # Extraemos el género del campo 'estilo_preferido' o lo inferimos
    # (En tu formulario guardamos "Mujer", "Hombre", "Niño" en estilo_preferido si no es un estilo concreto)
    genero_usuario = "Unisex" # Valor por defecto
    
    # Buscamos palabras clave en el texto de gustos o estilo para saber el género
    texto_analisis = (perfil.estilo_preferido + " " + perfil.gustos_texto).lower()
    
    if "mujer" in texto_analisis: genero_usuario = "Mujer"
    elif "hombre" in texto_analisis: genero_usuario = "Hombre"
    elif "niño" in texto_analisis or "niña" in texto_analisis: genero_usuario = "Nens/es" # Según tu BD

    perfil_texto = f"""
    Género Objetivo: {genero_usuario}
    Estilo: {perfil.estilo_preferido}
    Tallas: Superior {perfil.talla_superior}, Inferior {perfil.talla_inferior}
    Gustos: {perfil.gustos_texto}
    """

    # 2. PRE-FILTRADO INTELIGENTE (DB) 🧠
    # Solo sacamos productos que coincidan con la sección del usuario o sean Unisex
    # y que estén DISPONIBLES.
    
    filtro_seccion = Q(estado='DISPONIBLE')
    if perfil.presupuesto_rango:
        try:
            # Convertimos el texto de la BD a número decimal
            presupuesto_max = float(perfil.presupuesto_rango)
            
            # Aplicamos el filtro: precio <= presupuesto_max
            # Si el presupuesto es 0 o negativo, ignoramos el filtro
            if presupuesto_max > 0:
                filtro_seccion &= Q(precio__lte=presupuesto_max)
                
        except ValueError:
            pass # Si por error hay texto que no es número, no filtramos nada
    if genero_usuario == "Mujer":
        # Queremos productos de sección 'Dona' o 'Unisex'
        filtro_seccion &= (Q(seccion__iexact='Dona') | Q(seccion__iexact='Mujer') | Q(seccion__iexact='Unisex'))
    elif genero_usuario == "Hombre":
        # Queremos productos de sección 'Home' o 'Unisex'
        filtro_seccion &= (Q(seccion__iexact='Home') | Q(seccion__iexact='Hombre') | Q(seccion__iexact='Unisex'))
    elif genero_usuario == "Nens/es":
        filtro_seccion &= Q(seccion__icontains='Nens') # Busca 'Nens/es'

    # Aplicamos el filtro
    productos_candidatos = Products.objects.filter(filtro_seccion)
    
    
    print(f"DEBUG: Se han encontrado {productos_candidatos.count()} productos candidatos para este perfil.")
   

    lista_candidatos = list(productos_candidatos)
    # Si hay demasiados productos (ej. 1000), la IA se satura.
    # Cogemos una muestra aleatoria de 30 productos relevantes para que la IA elija entre esos.
    # Esto ahorra dinero y hace que la IA vaya más rápido.
    lista_candidatos = list(productos_candidatos)
    if len(lista_candidatos) > 30:
        lista_candidatos = random.sample(lista_candidatos, 30)

    # Preparamos el JSON para la IA
    catalogo_json = []
    for p in lista_candidatos:
        catalogo_json.append({
            "id": p.id,
            "nombre": p.nombre,
            "marca": p.marca,
            "tipo": p.subseccion, 
            "tags": p.tags_ia,
            "precio": float(p.precio)
        })

    # 3. El Prompt para Gemini (Ahora mucho más enfocado)
    prompt = f"""
    Eres Asterion, un Personal Shopper de moda.
    
    CLIENTE:
    {perfil_texto}
    
    CANDIDATOS SELECCIONADOS (JSON):
    {json.dumps(catalogo_json)}
    
    TU TAREA:
    De la lista de candidatos, selecciona los 5 MEJORES productos para crear un outfit completo.
    Intenta combinar una parte de arriba, una de abajo y accesorios/calzado si es posible.
    
    RESPUESTA (JSON puro):
    Devuelve SOLO una lista de IDs. Ejemplo: [12, 45, 33, 21, 9]
    """

    try:
        model = genai.GenerativeModel('gemini-flash-lateste')
        response = model.generate_content(prompt)
        
        texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
        ids_seleccionados = json.loads(texto_limpio)
        
        # 4. Recuperar objetos finales
        productos_finales = Products.objects.filter(id__in=ids_seleccionados)
        print(f'DEBUG: los de la IA {productos_finales.count()}')
        # Verificación de seguridad: Si la IA devuelve menos de 5, rellenamos
        lista_final = list(productos_finales)
        if len(lista_final) < 5 and len(lista_candidatos) >= 5:
            faltantes = 5 - len(lista_final)
            # Añadimos aleatorios de la lista de candidatos que no estén ya elegidos
            extras = [p for p in lista_candidatos if p not in lista_final][:faltantes]
            lista_final.extend(extras)
            
        return lista_final[:5] # Asegurar máximo 5

    except Exception as e:
        print(f"Error IA: {e}")
        # devolvemos 5 primeros candidatos del filtro (no totalmente aleatorios)
        return lista_candidatos[:5]
    
   
# En core/ai_logic.py

# ... imports anteriores ...
from .models import Products, StyleProfiles, Users # Asegúrate de importar Users también

def chat_con_asterion(mensaje_usuario, cliente_id, historial_chat=[]):
    """
    1. Busca los datos del usuario (Nombre, Estilo, Tallas).
    2. Configura a Gemini con esa "memoria".
    3. Responde al mensaje.
    """
    try:
        # A. RECUPERAR INFORMACIÓN DEL USUARIO
        contexto_usuario = "Información del cliente no disponible."
        nombre_usuario = "Viajero"
        
        if cliente_id:
            try:
                usuario = Users.objects.get(id=cliente_id)
                nombre_usuario = usuario.nombre
                
                perfil = StyleProfiles.objects.get(client_id=cliente_id)
                contexto_usuario = f"""
                - Nombre: {usuario.nombre}
                - Estilo Predominante: {perfil.estilo_preferido}
                - Tallas: Superior {perfil.talla_superior}, Inferior {perfil.talla_inferior}
                - Presupuesto: {perfil.presupuesto_rango}€
                - Notas personales: "{perfil.gustos_texto}"
                """
            except (Users.DoesNotExist, StyleProfiles.DoesNotExist):
                pass

        # B. CONFIGURAR EL MODELO (Con el contexto inyectado)
        model = genai.GenerativeModel('gemini-flash-latest') 
        
        prompt_sistema = f"""
        ACTÚA COMO: Asterion, el Personal Shopper Minotauro de 'MinosStore'.
        TONO: Elegante, mitológico pero moderno, servicial y experto.
        
        ESTÁS HABLANDO CON: {nombre_usuario}
        
        DATOS DEL CLIENTE (ÚSALOS PARA PERSONALIZAR TU RESPUESTA):
        {contexto_usuario}
        
        INSTRUCCIONES:
        1. Si te pregunta qué ponerse, basa tu respuesta en SU estilo y SUS tallas.
        2. No saludes presentándote en cada mensaje, sé natural.
        3. Sé breve (máximo 2-3 frases).
        """
        
        # C. LLAMAR A LA IA
        chat = model.start_chat(history=historial_chat)
        response = chat.send_message(f"{prompt_sistema}\n\nMENSAJE DEL CLIENTE: {mensaje_usuario}")
        
        return response.text

    except Exception as e:
        print(f"Error Chat: {e}")
        return "Mis sentidos de toro están nublados ahora mismo. Por favor, inténtalo de nuevo."