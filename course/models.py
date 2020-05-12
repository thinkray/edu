from django.core.validators import MinValueValidator
from django.db import models

from account.models import User
from storage.models import BlobStorage


class Course(models.Model):
    name = models.CharField(max_length=200)
    info = models.TextField(null=True)
    picture = models.ForeignKey(
        BlobStorage, on_delete=models.CASCADE, related_name='course_picture', blank=True, null=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='course_teacher')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quota = models.IntegerField(validators=[MinValueValidator(0)])
    sold = models.IntegerField(default=0, validators=[MinValueValidator(0)])


class CourseInstance(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='course_instance_course')
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='course_instance_student')
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='course_instance_teacher')
    quota = models.IntegerField(validators=[MinValueValidator(0)])
