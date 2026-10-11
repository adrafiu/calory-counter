from django.contrib import admin

from .models import FoodEntry, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "age", "gender", "height_cm", "weight_kg", "goal")
    list_filter = ("gender", "goal", "activity_level")
    search_fields = ("name", "user__username", "user__email")


@admin.register(FoodEntry)
class FoodEntryAdmin(admin.ModelAdmin):
    list_display = ("item_name", "calories", "user", "date")
    list_filter = ("date",)
    search_fields = ("item_name", "user__username")