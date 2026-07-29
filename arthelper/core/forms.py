from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(label='Логин', widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        if username and password:
            from django.contrib.auth import get_user_model
            UserModel = get_user_model()
            try:
                user = UserModel.objects.get(username=username)
            except UserModel.DoesNotExist:
                self.add_error('username', '')
                self.add_error('password', '')
                raise forms.ValidationError('Пользователь с таким логином не найден')
            if not user.check_password(password):
                self.add_error('password', '')
                raise forms.ValidationError('Неверный пароль')
            if not user.is_active:
                raise forms.ValidationError('Аккаунт неактивен')
            self.user_cache = user
            self.confirm_login_allowed(user)
        return self.cleaned_data


class RegisterForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=[('student', 'Студент'), ('teacher', 'Преподаватель')],
        label='Роль', widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_role'})
    )
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(
        label='Подтверждение пароля', widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    course = forms.ChoiceField(
    choices=[('', '— не выбран —')] + [(str(i), str(i)) for i in range(1, 7)],
    required=False,
    label='Курс',
    widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_course'})
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'role', 'faculty', 'education_level', 'course',
                  'degree', 'academic_rank', 'position', 'department']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'faculty': forms.Select(attrs={'class': 'form-select'}),
            'education_level': forms.Select(attrs={'class': 'form-select', 'id': 'id_education_level'}),
            'degree': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_rank': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'full_name': 'ФИО',
            'faculty': 'Факультет',
            'education_level': 'Уровень образования',
            'department': 'Кафедра',
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password_confirm'):
            raise forms.ValidationError('Пароли не совпадают')
        role = cleaned.get('role')
        if role == 'student':
            cleaned['degree'] = cleaned['academic_rank'] = cleaned['position'] = cleaned['department'] = ''
        elif role == 'teacher':
            cleaned['faculty'] = cleaned['education_level'] = ''
            cleaned['course'] = None  # ← вместо ''
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class ProfileUpdateForm(forms.ModelForm):
    course = forms.ChoiceField(
        choices=[('', '— не выбран —')],
        required=False, label='Курс', widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_course'})
    )

    class Meta:
        model = User
        fields = ['full_name', 'faculty', 'education_level', 'course',
                  'degree', 'academic_rank', 'position', 'department']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'faculty': forms.Select(attrs={'class': 'form-select'}),
            'education_level': forms.Select(attrs={'class': 'form-select', 'id': 'id_education_level'}),
            'degree': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_rank': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'full_name': 'ФИО',
            'faculty': 'Факультет',
            'education_level': 'Уровень образования',
            'department': 'Кафедра',
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # ← ВОТ ЭТО ГЛАВНОЕ: заполняем курсы в зависимости от уровня
        if user and user.role == 'student':
            limits = {
                'бакалавриат': 4,
                'специалитет': 5,
                'магистратура': 2,
                'аспирантура': 3
            }
            max_course = limits.get(user.education_level, 6)
            self.fields['course'].choices = [('', '— не выбран —')] + [
                (i, f'{i} курс') for i in range(1, max_course + 1)
            ]
            for fn in ['degree', 'academic_rank', 'position', 'department']:
                self.fields.pop(fn, None)
        elif user and user.role == 'teacher':
            for fn in ['faculty', 'education_level', 'course']:
                self.fields.pop(fn, None)