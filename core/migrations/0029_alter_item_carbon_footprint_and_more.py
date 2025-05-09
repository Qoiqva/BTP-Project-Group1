# Generated by Django 5.1.7 on 2025-04-13 02:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0028_promotion_products_alter_order_tracking_no'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='carbon_footprint',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='discount_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='item',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='order',
            name='tracking_no',
            field=models.CharField(default='9IK-Y11-7J0', max_length=150, null=True),
        ),
    ]
