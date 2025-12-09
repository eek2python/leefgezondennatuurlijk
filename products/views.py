from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Click


def homepage(request):
    return render(request, "index.html")

def snijplanken(request):
    return render(request, "snijplanken.html")

def koekenpannen(request):
    return render(request, "koekenpannen.html")

def hapjespannen(request):
    return render(request, "hapjespannen.html")

def wokpannen(request):
    return render(request, "wokpannen.html")

def airfryers(request):
    return render(request, "airfryers.html")

def vershoudcontainers(request):
    return render(request, "vershoudcontainers.html")

def blogs(request):
    return render(request, "blogs.html")

def blog01(request):
    return render(request, "blog-pfas-in-huis.html")
def product_list(request):
   products = Product.objects.filter(is_active=True)
   return render(request, "products/product_list.html", {"products": products})

def product_detail(request, slug):
   product = get_object_or_404(Product, slug=slug, is_active=True)
   return render(request, "products/product_detail.html", {"product": product})

def track_and_redirect(request, slug):
   product = get_object_or_404(Product, slug=slug, is_active=True)
   Click.objects.create(
       product=product,
       ip=request.META.get("REMOTE_ADDR"),
       user_agent=request.META.get("HTTP_USER_AGENT"),
   )
   return redirect(product.affiliate_url)