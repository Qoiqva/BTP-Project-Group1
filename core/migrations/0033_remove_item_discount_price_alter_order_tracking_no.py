# Generated by Django 5.1.7 on 2025-04-13 05:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0032_alter_order_tracking_no'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='discount_price',
        ),
        migrations.AlterField(
            model_name='order',
            name='tracking_no',
            field=models.CharField(default='NOI-NEZ-R8E', max_length=150, null=True),
        ),
    ]
