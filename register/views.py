from django.shortcuts import render, redirect
from .forms import RegisterForm


def register(response):
    if response.method == "POST":  # check if resposne was submitted by the user
        form = RegisterForm(response.POST)
        if form.is_valid(): # if we got all the responses we wanted?
            form.save()

        return redirect("/home")
    else:
        form = RegisterForm()

    return render(response, "register/register.html", {"form":form}) #Add an "invalid info" message