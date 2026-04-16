from django.contrib.auth.views import LoginView
from .forms import EmailAuthenticationForm


class CustomLoginView(LoginView):
    template_name = 'login.html'
    authentication_form = EmailAuthenticationForm

    def form_invalid(self, form):
        context = self.get_context_data(form=self.authentication_form(request=self.request))
        context['login_error'] = True
        return self.render_to_response(context)