# Generated by Django 5.1.7 on 2025-04-13 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0035_remove_item_discounted_price_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='tracking_no',
            field=models.CharField(default='FZ7-RU4-WEO', max_length=150, null=True),
        ),
    ]
