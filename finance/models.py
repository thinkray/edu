from django.db import models
from account.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Bill(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='bill_user')
    amount = models.DecimalField(max_digits=17, decimal_places=2)
    date = models.DateTimeField()
    info = models.TextField(null=True)


class RedemptionCode(models.Model):
    code = models.CharField(max_length=32, unique=True)
    amount = models.DecimalField(
        max_digits=17, decimal_places=2, validators=[MinValueValidator(0)])
    is_available = models.BooleanField()


class CouponCode(models.Model):
    code = models.CharField(max_length=32, unique=True)
    discount = models.DecimalField(max_digits=2, decimal_places=2, validators=[
                                   MinValueValidator(0.001), MaxValueValidator(0.999)])