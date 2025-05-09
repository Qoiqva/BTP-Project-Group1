# Generated by Django 5.1.7 on 2025-04-13 00:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0027_promotion_discount_rate_alter_order_tracking_no'),
    ]

    operations = [
        migrations.AddField(
            model_name='promotion',
            name='products',
            field=models.ManyToManyField(related_name='promotions', to='core.item'),
        ),
        migrations.AlterField(
            model_name='order',
            name='tracking_no',
            field=models.CharField(default='S9A-9SV-CGC', max_length=150, null=True),
        ),
    ]
