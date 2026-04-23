from django.urls import path
from .views import CustomLoginView, CustomPasswordChangeView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    # ログイン画面のURLパターン
    # ルートURL('')にアクセスすると、LoginViewが呼び出される
    # 'login.html'というテンプレートが表示される
    path('login/', CustomLoginView.as_view(), name='login'),

    # ログアウトのURLパターン
    # 'logout/'というURLにアクセスすると、LogoutViewが呼び出される
    path('logout/', LogoutView.as_view(), name='logout'),

    # パスワード変更
    path('password_change/', CustomPasswordChangeView.as_view(), name='password_change'),
]
