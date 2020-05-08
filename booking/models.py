from django.db import models

from account.models import User
from course.models import Course


class Booking(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='booking_teacher')
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='booking_student', null=True)
    info = models.TextField(null=True)
