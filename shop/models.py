from django.db import models

class Customer(models.Model):
    telegram_id = models.PositiveIntegerField(null=True)
    name = models.TextField(null=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=100,null=True)
    price = models.FloatField()

    def __str__(self):
        return self.name


class Cart(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(null=False)

class Order(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE,null=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(null=False)
    total = models.BigIntegerField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.payment.id
