from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Role


@receiver(post_save, sender=User)
def assign_default_role(sender, instance, created, **kwargs):
    """
    Automatically assign COMMON_USER role to every new user
    if they don't already have a role assigned.
    """
    if created and instance.role is None:
        try:
            default_role = Role.objects.get(name='COMMON_USER')
            instance.role = default_role
            instance.save(update_fields=['role'])
        except Role.DoesNotExist:
            pass  # Role not seeded yet — skip