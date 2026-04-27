from django import forms
from django.contrib.auth.forms import AuthenticationForm


class EmailAuthenticationForm(AuthenticationForm):
    error_messages = {
        "invalid_login": "ユーザーIDまたはパスワードが正しくありません。",
    }

    username = forms.EmailField(
        label="ユーザーID",
        error_messages={
            "required": "このフィールドは必須です。",
            "invalid": "正しいメールアドレスを入力してください。",
        },
    )

    password = forms.CharField(
        label="パスワード",
        widget=forms.PasswordInput,
        error_messages={
            "required": "このフィールドは必須です。",
        },
    )
