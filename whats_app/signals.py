from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Message, MessageStatus, Chat

@receiver(post_save, sender=Message)
def create_message_status(sender, instance, created, **kwargs):
    """Create message status for all chat participants except sender"""
    if created:
        participants = instance.chat.participants.exclude(user=instance.sender)
        for participant in participants:
            MessageStatus.objects.create(
                message=instance,
                user=participant.user,
                status='sent'
            )