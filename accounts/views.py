from django.shortcuts import render, redirect
from .forms import SignUpForm
from django.contrib.auth import login, authenticate

def register(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Log the user in immediately after registration (optional)
            login(request, user)
            return redirect('home')  # redirect to homepage or another page
    else:
        form = SignUpForm()
    return render(request, 'accounts/register.html', {'form': form})