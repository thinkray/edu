# Generated by Django 3.0.3 on 2020-05-08 07:48

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('storage', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('info', models.TextField(null=True)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('quota', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('sold', models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(0)])),
                ('picture', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='course_picture', to='storage.BlobStorage')),
                ('teacher', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_teacher', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CourseInstance',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quota', models.IntegerField(validators=[django.core.validators.MinValueValidator(0)])),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_instance_course', to='course.Course')),
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='course_instance_student', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
