import os
from django.http import HttpResponse
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime
def sitemap_xml(request):
   # Locatie van blog-templates
   blog_templates_path = os.path.join(settings.BASE_DIR, "blogs", "templates")
   blog_urls = []
   # Scan alle .html bestanden in de blogtemplate-map
   for filename in os.listdir(blog_templates_path):
       if filename.endswith(".html"):
           slug = filename.replace(".html", "")
           file_path = os.path.join(blog_templates_path, filename)
           blog_urls.append({
               "loc": f"https://leefnatuurlijkengezond.nl/blogs/{slug}/",
               "lastmod": datetime.fromtimestamp(
                   os.path.getmtime(file_path)
               ).strftime("%Y-%m-%d")
           })
   xml = render_to_string("sitemap_template.xml", {
       "blog_urls": blog_urls
   })
   return HttpResponse(xml, content_type="application/xml")