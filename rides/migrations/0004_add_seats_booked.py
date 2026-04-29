# Manual migration to add seats_booked field
from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('rides', '0003_auto_20260422_1259'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='seats_booked',
            field=models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]