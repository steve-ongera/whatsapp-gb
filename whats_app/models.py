from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class User(AbstractUser):
    phone_number = models.CharField(max_length=20, unique=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    about = models.CharField(max_length=139, default="Hey there! I'm using WhatsApp")
    is_online = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)
    qr_code = models.CharField(max_length=255, unique=True, null=True, blank=True)
    
    # Privacy Settings
    read_receipts = models.BooleanField(default=True)
    last_seen_privacy = models.CharField(max_length=20, default='everyone', 
                                        choices=[('everyone', 'Everyone'), 
                                                ('contacts', 'My Contacts'), 
                                                ('nobody', 'Nobody')])
    profile_photo_privacy = models.CharField(max_length=20, default='everyone',
                                            choices=[('everyone', 'Everyone'), 
                                                    ('contacts', 'My Contacts'), 
                                                    ('nobody', 'Nobody')])
    
    # App Settings
    theme = models.CharField(max_length=20, default='light', 
                            choices=[('light', 'Light'), ('dark', 'Dark')])
    wallpaper = models.ImageField(upload_to='wallpapers/', null=True, blank=True)
    font_size = models.CharField(max_length=10, default='medium',
                                choices=[('small', 'Small'), 
                                        ('medium', 'Medium'), 
                                        ('large', 'Large')])
    
    # Security
    app_lock_enabled = models.BooleanField(default=False)
    app_lock_pin = models.CharField(max_length=6, null=True, blank=True)
    fingerprint_enabled = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.phone_number


class Contact(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacts')
    contact_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='contacted_by')
    name = models.CharField(max_length=100)
    is_blocked = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'contact_user')

    def __str__(self):
        return f"{self.user.phone_number} - {self.name}"


class Chat(models.Model):
    CHAT_TYPES = [
        ('private', 'Private'),
        ('group', 'Group'),
    ]
    
    chat_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    chat_type = models.CharField(max_length=10, choices=CHAT_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.chat_type} - {self.chat_id}"


class ChatParticipant(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_muted = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    # Custom settings per chat
    custom_wallpaper = models.ImageField(upload_to='chat_wallpapers/', null=True, blank=True)
    custom_theme = models.CharField(max_length=20, null=True, blank=True)

    class Meta:
        unique_together = ('chat', 'user')

    def __str__(self):
        return f"{self.user.phone_number} in {self.chat.chat_id}"


class Group(models.Model):
    chat = models.OneToOneField(Chat, on_delete=models.CASCADE, related_name='group')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='group_icons/', null=True, blank=True)
    
    # Group Settings
    only_admins_can_send = models.BooleanField(default=False)
    only_admins_can_edit = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GroupAdmin(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='admins')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')


class Message(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('voice', 'Voice Note'),
        ('document', 'Document'),
        ('sticker', 'Sticker'),
        ('contact', 'Contact'),
        ('location', 'Location'),
    ]

    message_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES)
    content = models.TextField(blank=True)
    
    # Media files
    media_file = models.FileField(upload_to='media/', null=True, blank=True)
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    
    # Reply functionality
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    
    # Status
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.sender.phone_number}: {self.content[:50]}"


class MessageStatus(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
    ]
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='statuses')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('message', 'user')


class DeletedMessage(models.Model):
    """Track deleted messages so users can still see 'This message was deleted'"""
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    deleted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    deleted_for_everyone = models.BooleanField(default=False)
    original_content = models.TextField()
    deleted_at = models.DateTimeField(auto_now_add=True)


class TypingStatus(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_typing = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('chat', 'user')


class Call(models.Model):
    CALL_TYPES = [
        ('voice', 'Voice'),
        ('video', 'Video'),
    ]
    
    CALL_STATUS = [
        ('initiated', 'Initiated'),
        ('ringing', 'Ringing'),
        ('answered', 'Answered'),
        ('ended', 'Ended'),
        ('missed', 'Missed'),
        ('declined', 'Declined'),
    ]
    
    call_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='calls')
    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calls_made')
    call_type = models.CharField(max_length=10, choices=CALL_TYPES)
    status = models.CharField(max_length=20, choices=CALL_STATUS, default='initiated')
    
    started_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(default=0)  # in seconds

    def __str__(self):
        return f"{self.call_type} call - {self.call_id}"


class CallParticipant(models.Model):
    call = models.ForeignKey(Call, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('call', 'user')


class Status(models.Model):
    STATUS_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
    ]
    
    status_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='statuses')
    status_type = models.CharField(max_length=10, choices=STATUS_TYPES)
    content = models.TextField(blank=True)
    media_file = models.FileField(upload_to='status/', null=True, blank=True)
    background_color = models.CharField(max_length=7, default='#000000')
    font_style = models.CharField(max_length=50, default='normal')
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()  # 24 hours from creation

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.phone_number} - Status {self.status_id}"


class StatusView(models.Model):
    status = models.ForeignKey(Status, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('status', 'viewer')


class Community(models.Model):
    community_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='community_icons/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CommunityMember(models.Model):
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('community', 'user')


class CommunityGroup(models.Model):
    """Groups within a community"""
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='community_groups')
    group = models.ForeignKey(Group, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('community', 'group')


class Channel(models.Model):
    channel_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='channel_icons/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ChannelFollower(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='followers')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_muted = models.BooleanField(default=False)
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('channel', 'user')


class ChannelPost(models.Model):
    POST_TYPES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('poll', 'Poll'),
    ]
    
    post_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(blank=True)
    post_type = models.CharField(max_length=10, choices=POST_TYPES)
    media_file = models.FileField(upload_to='channel_posts/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.channel.name} - Post {self.post_id}"


class AIAssistant(models.Model):
    """AI Assistant for users who are bored"""
    assistant_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=50, default="WhatsApp AI")
    avatar = models.ImageField(upload_to='ai_avatars/', null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class AIConversation(models.Model):
    conversation_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations')
    assistant = models.ForeignKey(AIAssistant, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.phone_number} - AI Chat"


class AIMessage(models.Model):
    MESSAGE_TYPES = [
        ('text', 'Text'),
        ('voice', 'Voice'),
    ]
    
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    is_user = models.BooleanField(default=True)  # True if from user, False if from AI
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    content = models.TextField()
    audio_file = models.FileField(upload_to='ai_audio/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        sender = "User" if self.is_user else "AI"
        return f"{sender}: {self.content[:50]}"