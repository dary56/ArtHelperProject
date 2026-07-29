from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Journal, JournalTemplate


@login_required
def journal_create(request):
    if request.user.role != 'admin':
        return redirect('dashboard')
    if request.method == 'POST':
        title = request.POST.get('title')
        if title:
            Journal.objects.create(title=title)
            messages.success(request, 'Журнал добавлен!')
            return redirect('dashboard')
    return render(request, 'journals/journal_form.html')


@login_required
def journal_delete(request, pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    journal = get_object_or_404(Journal, pk=pk)
    journal.delete()
    messages.success(request, 'Журнал удалён!')
    return redirect('dashboard')


@login_required
def journal_detail(request, pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    journal = get_object_or_404(Journal, pk=pk)
    return render(request, 'journals/journal_detail.html', {'journal': journal})


@login_required
def template_add(request, journal_pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    journal = get_object_or_404(Journal, pk=journal_pk)
    if request.method == 'POST' and request.FILES.get('template_file'):
        JournalTemplate.objects.create(
            journal=journal,
            file=request.FILES['template_file']
        )
        messages.success(request, 'Шаблон загружен!')
        return redirect('journal_detail', pk=journal.pk)
    return render(request, 'journals/template_add.html', {'journal': journal})


@login_required
def template_delete(request, pk):
    if request.user.role != 'admin':
        return redirect('dashboard')
    template = get_object_or_404(JournalTemplate, pk=pk)
    journal_pk = template.journal.pk
    template.delete()
    messages.success(request, 'Шаблон удалён!')
    return redirect('journal_detail', pk=journal_pk)