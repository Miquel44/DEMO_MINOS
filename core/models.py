# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class OrderItems(models.Model):
    order = models.ForeignKey('Orders', models.DO_NOTHING, blank=True, null=True)
    product = models.ForeignKey('Products', models.DO_NOTHING, blank=True, null=True)
    se_queda_articulo = models.BooleanField(blank=True, null=True)
    motivo_devolucion = models.TextField(blank=True, null=True)
    valoracion = models.IntegerField(blank=True, null=True)
    comentario_valoracion = models.TextField(blank=True, null=True)
    fecha_valoracion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'order_items'


class Orders(models.Model):
    client = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    shopper = models.ForeignKey('Users', models.DO_NOTHING, related_name='orders_shopper_set', blank=True, null=True)
    fecha_pedido = models.DateTimeField(blank=True, null=True)
    estado = models.TextField(blank=True, null=True)  # This field type is a guess.
    tracking_code = models.CharField(max_length=50, blank=True, null=True)
    coste_servicio = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    es_primer_pedido = models.BooleanField(blank=True, null=True)
    total_final = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'orders'


class ProductRecommendations(models.Model):
    pk = models.CompositePrimaryKey('product_id', 'recommended_product_id')
    product = models.ForeignKey('Products', models.DO_NOTHING)
    recommended_product = models.ForeignKey('Products', models.DO_NOTHING, related_name='productrecommendations_recommended_product_set')

    class Meta:
        managed = False
        db_table = 'product_recommendations'


class Products(models.Model):
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True, null=True)
    seccion = models.CharField(max_length=100)
    subseccion = models.CharField(max_length=100, blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.TextField(blank=True, null=True)  # This field type is a guess.
    tags_ia = models.TextField(blank=True, null=True)
    image_url = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'products'


class StyleProfiles(models.Model):
    client = models.ForeignKey('Users', models.DO_NOTHING, blank=True, null=True)
    talla_superior = models.CharField(max_length=10, blank=True, null=True)
    talla_inferior = models.CharField(max_length=10, blank=True, null=True)
    estilo_preferido = models.CharField(max_length=100, blank=True, null=True)
    presupuesto_rango = models.CharField(max_length=50, blank=True, null=True)
    gustos_texto = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'style_profiles'


class Users(models.Model):
    nif = models.CharField(unique=True, max_length=20)
    nombre = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100, blank=True, null=True)
    email = models.CharField(unique=True, max_length=150)
    hashed_password = models.CharField(max_length=255)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    rol = models.TextField()  # This field type is a guess.
    fecha_registro = models.DateTimeField(blank=True, null=True)
    personal_shopper = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'users'
