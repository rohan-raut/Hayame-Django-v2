# Generated by Django 4.1 on 2024-06-14 12:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_frequencydiscount_rename_cost_addon_cost_per_hour_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cleanerbooking',
            name='addons',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='api.addon'),
        ),
    ]
