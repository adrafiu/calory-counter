from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from .models import FoodEntry, Profile


class BootstrapFormMixin:
    """প্রতিটা field-এ Bootstrap 5 class বসায়, যাতে template পরিষ্কার থাকে।"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.Select):
                css_class = "form-select"
            else:
                css_class = "form-control"
            field.widget.attrs.setdefault("class", css_class)


class RegisterForm(BootstrapFormMixin, forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["username", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["username"].help_text = ""
        self.fields["username"].widget.attrs["placeholder"] = "Choose a username"
        self.fields["email"].widget.attrs["placeholder"] = "you@example.com"
        self.fields["password"].widget.attrs["placeholder"] = "At least 6 characters"
        self.fields["confirm_password"].widget.attrs["placeholder"] = "Repeat password"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm = cleaned.get("confirm_password")
        if password and len(password) < 6:
            self.add_error("password", "Password must be at least 6 characters.")
        if password and confirm and password != confirm:
            self.add_error("confirm_password", "Passwords do not match.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(BootstrapFormMixin, forms.Form):
    identifier = forms.CharField(label="Username or email")
    password = forms.CharField(widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.fields["identifier"].widget.attrs["placeholder"] = "Username or email"
        self.fields["password"].widget.attrs["placeholder"] = "Your password"

    def clean(self):
        cleaned = super().clean()
        identifier = cleaned.get("identifier")
        password = cleaned.get("password")

        if identifier and password:
            username = identifier
            # email দিয়েও login করা যাবে
            if "@" in identifier:
                match = User.objects.filter(email__iexact=identifier).first()
                if match:
                    username = match.username

            self.user = authenticate(username=username, password=password)
            if self.user is None:
                raise forms.ValidationError("Wrong username/email or password.")
        return cleaned


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "name",
            "age",
            "gender",
            "height_cm",
            "weight_kg",
            "activity_level",
            "goal",
        ]
        labels = {"name": "Full name", "goal": "My goal"}


class FoodEntryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = FoodEntry
        fields = ["item_name", "calories"]
        labels = {"item_name": "Food item", "calories": "Calories (kcal)"}
        widgets = {
            "item_name": forms.TextInput(attrs={"placeholder": "e.g. Rice with chicken"}),
            "calories": forms.NumberInput(attrs={"placeholder": "e.g. 450", "min": 1}),
        }

    def clean_calories(self):
        calories = self.cleaned_data["calories"]
        if calories <= 0:
            raise forms.ValidationError("Calories must be more than zero.")
        return calories