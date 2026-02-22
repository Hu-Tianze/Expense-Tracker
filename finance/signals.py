# finance/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Transaction, AuditLog

@receiver(post_save, sender=Transaction)
def log_transaction_save(sender, instance, created, **kwargs):
    action = 'CREATE' if created else 'UPDATE'
    AuditLog.objects.create(
        user=instance.user,
        action=action,
        resource_type='Transaction',
        description=f"{action} transaction: {instance.amount_in_gbp} GBP ({instance.note or 'No note'})"
    )

@receiver(post_delete, sender=Transaction)
def log_transaction_delete(sender, instance, **kwargs):
    AuditLog.objects.create(
        user=instance.user,
        action='DELETE',
        resource_type='Transaction',
        description=f"Deleted transaction: {instance.amount_in_gbp} GBP"
    )