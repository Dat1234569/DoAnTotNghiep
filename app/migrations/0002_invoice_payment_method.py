from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="invoice",
            name="payment_method",
            field=models.CharField(
                choices=[("cash", "Tiền mặt"), ("qr", "Chuyển khoản QR")],
                default="cash",
                max_length=10,
            ),
        ),
    ]
