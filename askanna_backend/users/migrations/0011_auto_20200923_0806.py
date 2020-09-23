# Generated by Django 2.2.8 on 2020-09-23 08:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_auto_20200916_1017'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invitation',
            fields=[
                ('membership_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='users.Membership')),
                ('email', models.EmailField(max_length=254)),
                ('expiry_date', models.DateTimeField()),
            ],
            options={
                'abstract': False,
            },
            bases=('users.membership',),
        ),
        migrations.AlterField(
            model_name='membership',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='memberships', related_query_name='membership', to=settings.AUTH_USER_MODEL),
        ),
    ]
