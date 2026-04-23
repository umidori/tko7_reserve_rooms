import os

from django import forms
from django.contrib.auth.forms import AuthenticationForm

from .models import User, Department


class EmailAuthenticationForm(AuthenticationForm):
    error_messages = {
        'invalid_login': 'ユーザーIDまたはパスワードが正しくありません。',
    }

    username = forms.EmailField(
        label='ユーザーID',
        error_messages={
            'required': 'このフィールドは必須です。',
            'invalid': '正しいメールアドレスを入力してください。',
        }
    )

    password = forms.CharField(
        label='パスワード',
        widget=forms.PasswordInput,
        error_messages={
            'required': 'このフィールドは必須です。',
        }
    )


class UserCreateForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.all().order_by('name'),
        required=False,
        empty_label='（なし）',
        label='所属',
    )

    class Meta:
        model = User
        fields = ['login_id', 'name', 'role', 'department']
        labels = {
            'login_id':   'ユーザーID',
            'name':       '氏名',
            'role':       '権限',
            'department': '所属',
        }
        widgets = {
            'login_id': forms.TextInput(attrs={
                'placeholder': '半角英数字 50文字以内',
                'autocomplete': 'off',
            }),
            'name': forms.TextInput(attrs={
                'placeholder': '氏名を入力してください。',
            }),
            'role': forms.Select(),
        }

    def clean_login_id(self):
        login_id = self.cleaned_data.get('login_id', '').strip()
        if User.objects.filter(login_id=login_id).exists():
            raise forms.ValidationError('このユーザーIDはすでに使用されています。')
        return login_id


class UserUpdateForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.all().order_by('name'),
        required=False,
        empty_label='（なし）',
        label='所属',
    )

    class Meta:
        model = User
        fields = ['name', 'role', 'department']
        labels = {
            'name':       '氏名',
            'role':       '権限',
            'department': '所属',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': '氏名を入力してください。',
            }),
            'role': forms.Select(),
        }


class CSVUploadForm(forms.Form):
    CSV_MAX_SIZE = 5 * 1024 * 1024  # 5MB

    csv_file = forms.FileField(
        label='CSVファイル',
        error_messages={
            'required': 'CSVファイルを選択してください。',
        },
    )

    def clean_csv_file(self):
        f = self.cleaned_data.get('csv_file')
        if not f:
            return f

        ext = os.path.splitext(f.name)[1].lower()
        if ext != '.csv':
            raise forms.ValidationError('CSVファイル（.csv）をアップロードしてください。')

        allowed_mime = (
            'text/csv',
            'text/plain',
            'application/csv',
            'application/octet-stream',
        )
        if hasattr(f, 'content_type') and f.content_type not in allowed_mime:
            raise forms.ValidationError('CSVファイルをアップロードしてください。')

        if f.size > self.CSV_MAX_SIZE:
            raise forms.ValidationError('ファイルサイズが上限（5MB）を超えています。')

        return f
