# core/forms.py
from django import forms
from .models import Users

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
    # Campos visuales extra
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repite contraseña'}))
    
    # Tu BD obliga a tener NIF
    nif = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Users
        fields = ['nombre', 'apellidos', 'email', 'nif', 'telefono']
        
        # AQUI ESTABA EL ERROR. Fíjate que ahora pone EmailInput
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'}),
            'apellidos': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}), # <--- CORREGIDO: EmailInput
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        pwd = cleaned_data.get("password")
        confirm = cleaned_data.get("confirm_password")

        if pwd and confirm and pwd != confirm:
            self.add_error('confirm_password', "Las contraseñas no coinciden")
        return cleaned_data