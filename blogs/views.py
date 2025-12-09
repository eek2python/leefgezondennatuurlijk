from django.shortcuts import render
from django.http import Http404

def blogs_overview(request):
   return render(request, "blogs/blogoverzicht.html")

def blogs_detail(request, slug):
   template_name = f"blogs/{slug}.html"
   try:
       return render(request, template_name)
   except:
       raise Http404("Pagina niet gevonden")

# Create your views here.
