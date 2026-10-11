from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Profile(models.Model):
    GENDER_CHOICES = [
        ("M", "Male"),
        ("F", "Female"),
    ]

    ACTIVITY_CHOICES = [
        ("sedentary", "Sedentary (little or no exercise)"),
        ("light", "Lightly active (1-3 days/week)"),
        ("moderate", "Moderately active (3-5 days/week)"),
        ("active", "Very active (6-7 days/week)"),
        ("extra", "Extra active (hard exercise / physical job)"),
    ]

    GOAL_CHOICES = [
        ("maintain", "Maintain my weight"),
        ("lose", "Lose weight"),
        ("gain", "Gain weight"),
    ]

    # BMR-কে এই সংখ্যা দিয়ে গুণ করলে দৈনিক ক্যালরি প্রয়োজন পাওয়া যায়
    ACTIVITY_FACTORS = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "extra": 1.9,
    }

    # সহজ নিয়ম: দিনে প্রায় 500 kcal = সপ্তাহে প্রায় 0.5 kg
    GOAL_ADJUSTMENT = {
        "maintain": 0,
        "lose": -500,
        "gain": 500,
    }

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    name = models.CharField(max_length=100)
    age = models.PositiveIntegerField(
        validators=[MinValueValidator(10), MaxValueValidator(100)]
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    height_cm = models.FloatField(
        "Height (cm)", validators=[MinValueValidator(50), MaxValueValidator(250)]
    )
    weight_kg = models.FloatField(
        "Weight (kg)", validators=[MinValueValidator(20), MaxValueValidator(300)]
    )
    activity_level = models.CharField(
        max_length=20, choices=ACTIVITY_CHOICES, default="sedentary"
    )
    goal = models.CharField(max_length=10, choices=GOAL_CHOICES, default="maintain")

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    @property
    def bmr(self):
        """Job description-এর দুটো formula অনুযায়ী BMR।"""
        if self.gender == "M":
            value = (
                66.47
                + (13.75 * self.weight_kg)
                + (5.003 * self.height_cm)
                - (6.755 * self.age)
            )
        else:
            value = (
                655.1
                + (9.563 * self.weight_kg)
                + (1.850 * self.height_cm)
                - (4.676 * self.age)
            )
        return round(value)

    @property
    def maintenance_calories(self):
        """বর্তমান ওজন ধরে রাখতে দিনে কত ক্যালরি লাগবে।"""
        return round(self.bmr * self.ACTIVITY_FACTORS[self.activity_level])

    @property
    def target_calories(self):
        """Goal (কমানো/বাড়ানো) হিসাব করে দৈনিক টার্গেট।"""
        target = self.maintenance_calories + self.GOAL_ADJUSTMENT[self.goal]
        # শরীরের basal প্রয়োজনের নিচে নামতে বলব না
        return max(target, self.bmr)


class FoodEntry(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="food_entries"
    )
    item_name = models.CharField(max_length=120)
    calories = models.PositiveIntegerField()
    date = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "food entries"

    def __str__(self):
        return f"{self.item_name} - {self.calories} kcal"