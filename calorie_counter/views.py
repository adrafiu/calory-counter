from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import FoodEntryForm, LoginForm, ProfileForm, RegisterForm
from .models import FoodEntry, Profile


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Account created! Tell us a bit about yourself.")
        return redirect("profile")

    return render(request, "calorie_counter/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = LoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.user)
        next_url = request.GET.get("next", "")
        if next_url and url_has_allowed_host_and_scheme(next_url, request.get_host()):
            return redirect(next_url)
        return redirect("dashboard")

    return render(request, "calorie_counter/login.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


@login_required
def profile_view(request):
    profile = Profile.objects.filter(user=request.user).first()
    form = ProfileForm(request.POST or None, instance=profile)

    if request.method == "POST" and form.is_valid():
        saved = form.save(commit=False)
        saved.user = request.user
        saved.save()
        messages.success(request, "Your details are saved.")
        return redirect("dashboard")

    return render(
        request,
        "calorie_counter/profile.html",
        {"form": form, "is_new": profile is None},
    )


def get_progress_status(percent):
    if percent > 100:
        return "danger"
    if percent >= 85:
        return "warning"
    return "success"


@login_required
def dashboard_view(request):
    profile = Profile.objects.filter(user=request.user).first()
    if profile is None:
        messages.info(request, "Please fill in your details first.")
        return redirect("profile")

    today = timezone.localdate()

    form = FoodEntryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        entry = form.save(commit=False)
        entry.user = request.user
        entry.date = today
        entry.save()
        messages.success(request, f"{entry.item_name} added.")
        return redirect("dashboard")

    entries = FoodEntry.objects.filter(user=request.user, date=today)
    consumed = entries.aggregate(total=Sum("calories"))["total"] or 0
    target = profile.target_calories
    remaining = target - consumed
    percent = round(consumed / target * 100) if target else 0

    # শেষ ৭ দিনের সারাংশ
    week_start = today - timedelta(days=6)
    rows = (
        FoodEntry.objects.filter(user=request.user, date__gte=week_start)
        .order_by()
        .values("date")
        .annotate(total=Sum("calories"))
    )
    totals = {row["date"]: row["total"] for row in rows}

    week = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        day_total = totals.get(day, 0)
        day_percent = round(day_total / target * 100) if target else 0
        week.append(
            {
                "date": day,
                "total": day_total,
                "percent": min(day_percent, 100),
                "status": get_progress_status(day_percent),
            }
        )

    context = {
        "profile": profile,
        "form": form,
        "entries": entries,
        "consumed": consumed,
        "target": target,
        "remaining": remaining,
        "over_by": abs(remaining),
        "percent": min(percent, 100),
        "status": get_progress_status(percent),
        "week": week,
        "today": today,
    }
    return render(request, "calorie_counter/dashboard.html", context)


@login_required
@require_POST
def delete_entry(request, pk):
    entry = get_object_or_404(FoodEntry, pk=pk, user=request.user)
    entry.delete()
    messages.info(request, "Entry removed.")
    return redirect("dashboard")