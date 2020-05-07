from django.db import models
from account.models import User
from course.models import Course


class Booking(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date = models.DateTimeField()
    teacher = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='booking_teacher')
    student = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='booking_student', null=True)
    is_full = models.BooleanField()
    info = models.TextField(null=True)

    def __str__(self):
        return self.course + ':' + self.teacher + ':' + self.student + ':' + self.date
