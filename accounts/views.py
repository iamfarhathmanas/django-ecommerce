from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView

from .forms import AddressForm, ProfileForm, SignupForm
from .models import Address


class SignupView(FormView):
    template_name = "accounts/signup.html"
    form_class = SignupForm
    success_url = reverse_lazy("store:home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, "Welcome to the store!")
        return super().form_valid(form)


class UserLoginView(LoginView):
    template_name = "accounts/login.html"


class UserLogoutView(LogoutView):
    next_page = reverse_lazy("store:home")


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["profile_form"] = ProfileForm(instance=self.request.user)
        context["address_form"] = AddressForm()
        context["addresses"] = self.request.user.addresses.all()
        return context

    def post(self, request, *args, **kwargs):
        if "profile_form" in request.POST:
            form = ProfileForm(request.POST, request.FILES, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, "Profile updated.")
                return redirect("accounts:profile")
        elif "address_form" in request.POST:
            form = AddressForm(request.POST)
            if form.is_valid():
                Address.objects.create(user=request.user, **form.cleaned_data)
                messages.success(request, "Address saved.")
                return redirect("accounts:profile")
        messages.error(request, "Please fix the errors below.")
        return self.get(request, *args, **kwargs)
