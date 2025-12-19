from django.db import models

class Wallet(models.Model):
    mnemonic = models.TextField()
    private_key = models.CharField(max_length=255)
    public_key = models.CharField(max_length=255)
    address = models.CharField(max_length=42, unique=True)
    derivation_path = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address