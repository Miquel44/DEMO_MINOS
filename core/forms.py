# core/forms.py
from django import forms
from .models import Users, StyleProfiles

# --- LISTAS DE OPCIONES (Definidas fuera para evitar errores) ---
TALLAS_ROPA = [('', 'Selecciona...'), ('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL')]
TALLAS_PANTALON = [('', 'Selecciona...'), ('34', '34'), ('36', '36'), ('38', '38'), ('40', '40'), ('42', '42'), ('44', '44'), ('46', '46')]
GENERO_CHOICES = [('Mujer', 'Mujer'), ('Hombre', 'Hombre'), ('Niño', 'Niño/a')]

class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Email", 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'nombre@ejemplo.com'})
    )
    password = forms.CharField(
        label="Password", 
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '******'})
    )

class RegistroForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite contraseña'}))
    nif = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Users
        fields = ['nombre', 'apellidos', 'email', 'nif', 'telefono']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if pwd and confirm and pwd != confirm:
            self.add_error('confirm_password', "Las contraseñas no coinciden")
        return cleaned_data

class PerfilEstiloForm(forms.ModelForm):
    # Campo extra para el género
    genero = forms.ChoiceField(choices=GENERO_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = StyleProfiles
        fields = ['talla_superior', 'talla_inferior', 'presupuesto_rango', 'gustos_texto']
        
        widgets = {
            'talla_superior': forms.Select(choices=TALLAS_ROPA, attrs={'class': 'form-select'}),
            'talla_inferior': forms.Select(choices=TALLAS_PANTALON, attrs={'class': 'form-select'}),
            
            # --- CAMBIO AQUÍ: NumberInput ---
            'presupuesto_rango': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 50 (Euros máximo por prenda)'}),
            
            'gustos_texto': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Ej: Me gusta el estilo casual...'}),
        }