from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0002_invoice_payment_method"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="paid_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
