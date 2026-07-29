from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm, RegisterForm, ProfileUpdateForm


def index_view(request):
    return render(request, 'core/index.html')


def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()  # ← только создаём пользователя, НЕ авторизуем
            messages.success(request, 'Регистрация прошла успешно! Теперь вы можете войти.')
            return redirect('index')  # ← на главную страницу, а не в кабинет
    else:
        form = RegisterForm()
    return render(request, 'core/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
    else:
        form = LoginForm()
    return render(request, 'core/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('index')


@login_required
def dashboard_view(request):
    articles = request.user.articles.prefetch_related('metadata', 'metadata__journal').all()
    context = {
        'user': request.user,
        'articles': articles,
    }
    if request.user.role == 'admin':
        from journals.models import Journal
        context['journals'] = Journal.objects.prefetch_related('templates').all()
    return render(request, 'core/dashboard.html', context)


@login_required
def profile_edit_view(request):
    if request.user.role == 'admin':
        return redirect('dashboard')
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, instance=request.user, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Данные успешно обновлены!')
            return redirect('dashboard')
    else:
        form = ProfileUpdateForm(instance=request.user, user=request.user)
    return render(request, 'core/profile_edit.html', {'form': form})