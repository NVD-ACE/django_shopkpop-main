# Generated by Django 5.1.7 on 2025-03-21 12:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product', '0008_alter_sanpham_motadai'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sanpham',
            name='PhanTramGiam',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
