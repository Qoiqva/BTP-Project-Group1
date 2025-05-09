# Generated by Django 5.1.7 on 2025-04-14 15:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0037_item_discounted_price_alter_order_tracking_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='first_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='last_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='tracking_no',
            field=models.CharField(default='HG2-61J-VHN', max_length=150, null=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='phone',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
