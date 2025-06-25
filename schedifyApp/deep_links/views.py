from django.shortcuts import render


def deep_link_test_view(request):
    return render(request, "deep_link_test.html")