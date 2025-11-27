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
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        
        texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
        ids_seleccionados = json.loads(texto_limpio)
        
        # 4. Recuperar objetos finales
        productos_finales = Products.objects.filter(id__in=ids_seleccionados)
        
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
        # Fallback inteligente: devolvemos 5 primeros candidatos del filtro (no totalmente aleatorios)
        return lista_candidatos[:5]
    
    # core/ai_logic.py

def chat_con_asterion(mensaje_usuario, historial_chat=[]):
    """
    1. Recibe el mensaje del usuario.
    2. Envía el contexto a Gemini.
    3. Devuelve la respuesta de Asterion.
    """
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Construimos el prompt de sistema para darle personalidad
        prompt_sistema = """
        Eres Asterion, un Personal Shopper exclusivo de la tienda de moda 'MinosStore'.
        Tu avatar es un minotauro elegante.
        Tu tono es: Profesional, sofisticado, un poco mitológico pero muy servicial y experto en moda.
        
        OBJETIVO: Ayudar al cliente con dudas de estilo, preguntas sobre su pedido o devoluciones.
        NO INVENTES datos de pedidos específicos (si te preguntan "¿dónde está mi pedido?", diles que lo miren en la sección 'Mis Pedidos').
        Sé conciso (máximo 3 frases).
        """
        
        # Creamos el chat con el historial previo (si existe)
        chat = model.start_chat(history=historial_chat)
        
        # Enviamos el mensaje con el contexto del sistema
        response = chat.send_message(f"{prompt_sistema}\n\nUsuario dice: {mensaje_usuario}")
        
        return response.text

    except Exception as e:
        print(f"Error Chat: {e}")
        return "Lo siento, los astros no están alineados ahora mismo. Inténtalo más tarde."