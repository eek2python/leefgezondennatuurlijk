from django.db import models
class Category(models.Model):
   name = models.CharField(max_length=100)
   slug = models.SlugField(unique=True)
   def __str__(self):
       return self.name

class Product(models.Model):
   title = models.CharField(max_length=255)
   slug = models.SlugField(unique=True)
   description = models.TextField(blank=True)
   affiliate_url = models.URLField()
   category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
   is_active = models.BooleanField(default=True)
   created = models.DateTimeField(auto_now_add=True)
   updated = models.DateTimeField(auto_now=True)
   def __str__(self):
       return self.title

class Click(models.Model):
   product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="clicks")
   timestamp = models.DateTimeField(auto_now_add=True)
   ip = models.GenericIPAddressField(null=True, blank=True)
   user_agent = models.CharField(max_length=1024, blank=True)
