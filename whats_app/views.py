from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Max
from django.utils import timezone
from django.core.files.storage import default_storage
import uuid
import qrcode
from io import BytesIO
import base64
import json
from .models import *


def generate_qr_code(user):
    """Generate QR code for WhatsApp Web login"""
    qr_data = str(uuid.uuid4())
    user.qr_code = qr_data
    user.save()
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()


def login_page(request):
    """Login with phone number"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        
        user = authenticate(request, username=phone_number, password=password)
        if user:
            login(request, user)
            user.is_online = True
            user.save()
            return redirect('chat_home')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    
    return render(request, 'login.html')


def register(request):
    """Create WhatsApp account"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        password = request.POST.get('password')
        username = request.POST.get('username')
        
        if User.objects.filter(phone_number=phone_number).exists():
            return render(request, 'register.html', {'error': 'Phone number already registered'})
        
        user = User.objects.create_user(
            username=username,
            phone_number=phone_number,
            password=password
        )
        login(request, user)
        return redirect('chat_home')
    
    return render(request, 'register.html')


def qr_login(request):
    """QR Code login for web/laptop"""
    if request.method == 'POST':
        qr_code = request.POST.get('qr_code')
        phone_number = request.POST.get('phone_number')
        
        try:
            user = User.objects.get(phone_number=phone_number, qr_code=qr_code)
            login(request, user)
            user.is_online = True
            user.qr_code = None  # Invalidate QR after use
            user.save()
            return JsonResponse({'success': True})
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid QR code'})
    
    # Generate QR for scanning
    qr_image = generate_qr_code(request.user) if request.user.is_authenticated else None
    return render(request, 'qr_login.html', {'qr_image': qr_image})


@login_required
def chat_home(request):
    """Main chat interface"""
    # Get all chats for the user
    chat_participants = ChatParticipant.objects.filter(
        user=request.user
    ).select_related('chat').order_by('-chat__updated_at')
    
    chats_data = []
    for participant in chat_participants:
        chat = participant.chat
        
        # Get last message
        last_message = Message.objects.filter(
            chat=chat
        ).order_by('-created_at').first()
        
        # Get unread count
        unread_count = Message.objects.filter(
            ~Q(sender=request.user),
            chat=chat
        ).exclude(
            statuses__user=request.user,
            statuses__status='read'
        ).count()
        
        # Get chat name and photo
        if chat.chat_type == 'private':
            other_participant = chat.participants.exclude(user=request.user).first()
            if other_participant:
                contact = Contact.objects.filter(
                    user=request.user,
                    contact_user=other_participant.user
                ).first()
                
                chat_name = contact.name if contact else other_participant.user.phone_number
                chat_photo = other_participant.user.profile_picture.url if other_participant.user.profile_picture else None
                is_online = other_participant.user.is_online
        else:
            group = chat.group
            chat_name = group.name
            chat_photo = group.icon.url if group.icon else None
            is_online = False
        
        chats_data.append({
            'chat': chat,
            'participant': participant,
            'last_message': last_message,
            'unread_count': unread_count,
            'name': chat_name,
            'photo': chat_photo,
            'is_online': is_online,
        })
    
    context = {
        'chats': chats_data,
        'user': request.user,
    }
    
    return render(request, 'chat_home.html', context)


@login_required
def chat_view(request, chat_id):
    """Individual chat view"""
    chat = get_object_or_404(Chat, chat_id=chat_id)
    
    # Verify user is participant
    participant = get_object_or_404(ChatParticipant, chat=chat, user=request.user)
    
    # Get messages
    messages = Message.objects.filter(chat=chat).order_by('created_at')
    
    # Mark messages as read
    MessageStatus.objects.filter(
        message__chat=chat,
        user=request.user
    ).update(status='read', timestamp=timezone.now())
    
    # Get chat info
    if chat.chat_type == 'private':
        other_participant = chat.participants.exclude(user=request.user).first()
        contact = Contact.objects.filter(
            user=request.user,
            contact_user=other_participant.user
        ).first()
        
        chat_name = contact.name if contact else other_participant.user.phone_number
        chat_photo = other_participant.user.profile_picture.url if other_participant.user.profile_picture else None
        is_online = other_participant.user.is_online
        last_seen = other_participant.user.last_seen
    else:
        group = chat.group
        chat_name = group.name
        chat_photo = group.icon.url if group.icon else None
        is_online = False
        last_seen = None
    
    context = {
        'chat': chat,
        'messages': messages,
        'chat_name': chat_name,
        'chat_photo': chat_photo,
        'is_online': is_online,
        'last_seen': last_seen,
        'participant': participant,
    }
    
    return render(request, 'chat_view.html', context)


@login_required
def new_chat(request):
    """Start a new chat with phone number"""
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        
        try:
            contact_user = User.objects.get(phone_number=phone_number)
            
            # Check if chat already exists
            existing_chat = Chat.objects.filter(
                chat_type='private',
                participants__user=request.user
            ).filter(
                participants__user=contact_user
            ).first()
            
            if existing_chat:
                return redirect('chat_view', chat_id=existing_chat.chat_id)
            
            # Create new chat
            chat = Chat.objects.create(chat_type='private')
            ChatParticipant.objects.create(chat=chat, user=request.user)
            ChatParticipant.objects.create(chat=chat, user=contact_user)
            
            # Add to contacts if not already
            Contact.objects.get_or_create(
                user=request.user,
                contact_user=contact_user,
                defaults={'name': contact_user.username}
            )
            
            return redirect('chat_view', chat_id=chat.chat_id)
        
        except User.DoesNotExist:
            return render(request, 'new_chat.html', {'error': 'User not found on WhatsApp'})
    
    return render(request, 'new_chat.html')


@login_required
@require_http_methods(["POST"])
def send_message(request):
    """Send a message via AJAX"""
    data = json.loads(request.body)
    chat_id = data.get('chat_id')
    content = data.get('content')
    message_type = data.get('message_type', 'text')
    reply_to_id = data.get('reply_to')
    
    chat = get_object_or_404(Chat, chat_id=chat_id)
    
    # Check if user can send (group permissions)
    if chat.chat_type == 'group':
        group = chat.group
        if group.only_admins_can_send:
            is_admin = GroupAdmin.objects.filter(group=group, user=request.user).exists()
            if not is_admin:
                return JsonResponse({'success': False, 'error': 'Only admins can send messages'})
    
    reply_to = None
    if reply_to_id:
        reply_to = Message.objects.get(message_id=reply_to_id)
    
    message = Message.objects.create(
        chat=chat,
        sender=request.user,
        message_type=message_type,
        content=content,
        reply_to=reply_to
    )
    
    # Create status for all participants
    participants = chat.participants.all()
    for participant in participants:
        if participant.user != request.user:
            MessageStatus.objects.create(
                message=message,
                user=participant.user,
                status='sent'
            )
    
    return JsonResponse({
        'success': True,
        'message_id': str(message.message_id),
        'timestamp': message.created_at.isoformat()
    })


@login_required
@require_http_methods(["POST"])
def delete_message(request):
    """Delete message"""
    data = json.loads(request.body)
    message_id = data.get('message_id')
    delete_for_everyone = data.get('delete_for_everyone', False)
    
    message = get_object_or_404(Message, message_id=message_id, sender=request.user)
    
    # Save original content for "This message was deleted"
    DeletedMessage.objects.create(
        message=message,
        deleted_by=request.user,
        deleted_for_everyone=delete_for_everyone,
        original_content=message.content
    )
    
    message.is_deleted = True
    message.deleted_at = timezone.now()
    if delete_for_everyone:
        message.content = "This message was deleted"
    message.save()
    
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["POST"])
def edit_message(request):
    """Edit message"""
    data = json.loads(request.body)
    message_id = data.get('message_id')
    new_content = data.get('content')
    
    message = get_object_or_404(Message, message_id=message_id, sender=request.user)
    message.content = new_content
    message.is_edited = True
    message.edited_at = timezone.now()
    message.save()
    
    return JsonResponse({'success': True})


@login_required
def create_group(request):
    """Create a new group"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        participant_ids = request.POST.getlist('participants')
        
        # Create chat and group
        chat = Chat.objects.create(chat_type='group')
        group = Group.objects.create(
            chat=chat,
            name=name,
            description=description,
            created_by=request.user
        )
        
        # Add creator as participant and admin
        ChatParticipant.objects.create(chat=chat, user=request.user)
        GroupAdmin.objects.create(group=group, user=request.user)
        
        # Add other participants
        for user_id in participant_ids:
            user = User.objects.get(id=user_id)
            ChatParticipant.objects.create(chat=chat, user=user)
        
        return redirect('chat_view', chat_id=chat.chat_id)
    
    # Get contacts
    contacts = Contact.objects.filter(user=request.user)
    return render(request, 'create_group.html', {'contacts': contacts})


@login_required
@require_http_methods(["POST"])
def block_user(request):
    """Block a user"""
    data = json.loads(request.body)
    user_id = data.get('user_id')
    
    contact_user = get_object_or_404(User, id=user_id)
    contact, created = Contact.objects.get_or_create(
        user=request.user,
        contact_user=contact_user,
        defaults={'name': contact_user.username}
    )
    contact.is_blocked = True
    contact.save()
    
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["POST"])
def pin_chat(request):
    """Pin/unpin a chat"""
    data = json.loads(request.body)
    chat_id = data.get('chat_id')
    is_pinned = data.get('is_pinned', True)
    
    chat = get_object_or_404(Chat, chat_id=chat_id)
    participant = get_object_or_404(ChatParticipant, chat=chat, user=request.user)
    participant.is_pinned = is_pinned
    participant.save()
    
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["POST"])
def archive_chat(request):
    """Archive/unarchive a chat"""
    data = json.loads(request.body)
    chat_id = data.get('chat_id')
    is_archived = data.get('is_archived', True)
    
    chat = get_object_or_404(Chat, chat_id=chat_id)
    participant = get_object_or_404(ChatParticipant, chat=chat, user=request.user)
    participant.is_archived = is_archived
    participant.save()
    
    return JsonResponse({'success': True})


@login_required
def settings_view(request):
    """User settings"""
    if request.method == 'POST':
        # Update settings
        request.user.theme = request.POST.get('theme', 'light')
        request.user.font_size = request.POST.get('font_size', 'medium')
        request.user.read_receipts = request.POST.get('read_receipts') == 'on'
        request.user.app_lock_enabled = request.POST.get('app_lock_enabled') == 'on'
        
        if request.POST.get('app_lock_pin'):
            request.user.app_lock_pin = request.POST.get('app_lock_pin')
        
        if request.FILES.get('wallpaper'):
            request.user.wallpaper = request.FILES['wallpaper']
        
        if request.FILES.get('profile_picture'):
            request.user.profile_picture = request.FILES['profile_picture']
        
        request.user.save()
        
        return redirect('settings')
    
    return render(request, 'settings.html', {'user': request.user})


@login_required
def status_view(request):
    """View statuses"""
    # Get active statuses (not expired)
    contacts = Contact.objects.filter(user=request.user)
    contact_users = [c.contact_user for c in contacts]
    
    statuses = Status.objects.filter(
        user__in=contact_users,
        expires_at__gt=timezone.now()
    ).order_by('-created_at')
    
    my_statuses = Status.objects.filter(
        user=request.user,
        expires_at__gt=timezone.now()
    ).order_by('-created_at')
    
    return render(request, 'status.html', {
        'statuses': statuses,
        'my_statuses': my_statuses
    })


@login_required
@require_http_methods(["POST"])
def create_status(request):
    """Create a new status"""
    status_type = request.POST.get('status_type', 'text')
    content = request.POST.get('content', '')
    
    status = Status.objects.create(
        user=request.user,
        status_type=status_type,
        content=content
    )
    
    if request.FILES.get('media_file'):
        status.media_file = request.FILES['media_file']
        status.save()
    
    return JsonResponse({'success': True, 'status_id': str(status.status_id)})


@login_required
def ai_chat(request):
    """AI Assistant chat"""
    assistant = AIAssistant.objects.first()
    if not assistant:
        assistant = AIAssistant.objects.create()
    
    conversation, created = AIConversation.objects.get_or_create(
        user=request.user,
        assistant=assistant
    )
    
    messages = AIMessage.objects.filter(conversation=conversation).order_by('created_at')
    
    return render(request, 'ai_chat.html', {
        'conversation': conversation,
        'messages': messages,
        'assistant': assistant
    })


@login_required
@require_http_methods(["POST"])
def send_ai_message(request):
    """Send message to AI"""
    data = json.loads(request.body)
    conversation_id = data.get('conversation_id')
    content = data.get('content')
    
    conversation = get_object_or_404(AIConversation, conversation_id=conversation_id, user=request.user)
    
    # Save user message
    user_message = AIMessage.objects.create(
        conversation=conversation,
        is_user=True,
        content=content
    )
    
    # Generate AI response (integrate with Claude API here)
    ai_response = generate_ai_response(content)
    
    ai_message = AIMessage.objects.create(
        conversation=conversation,
        is_user=False,
        content=ai_response
    )
    
    return JsonResponse({
        'success': True,
        'ai_response': ai_response,
        'timestamp': ai_message.created_at.isoformat()
    })


def generate_ai_response(user_message):
    """Generate AI response using Claude API"""
    # This would integrate with Anthropic's Claude API
    # For now, a simple response
    return f"I received your message: '{user_message}'. How can I help you today?"


@login_required
def logout_view(request):
    """Logout user"""
    request.user.is_online = False
    request.user.save()
    logout(request)
    return redirect('login')



# Updated views.py for AI integration
from .ai_service import ClaudeAIService

ai_service = ClaudeAIService()

@login_required
@require_http_methods(["POST"])
def send_ai_message(request):
    """Send message to AI with Claude integration"""
    data = json.loads(request.body)
    conversation_id = data.get('conversation_id')
    content = data.get('content')
    message_type = data.get('message_type', 'text')
    
    conversation = get_object_or_404(
        AIConversation, 
        conversation_id=conversation_id, 
        user=request.user
    )
    
    # Save user message
    user_message = AIMessage.objects.create(
        conversation=conversation,
        is_user=True,
        content=content,
        message_type=message_type
    )
    
    # Get conversation history (last 10 messages for context)
    history = AIMessage.objects.filter(
        conversation=conversation
    ).order_by('-created_at')[:10][::-1]
    
    # Generate AI response
    if message_type == 'voice':
        response_data = ai_service.generate_voice_response(content, history)
        ai_response = response_data['text']
        audio_url = response_data['audio_url']
        
        ai_message = AIMessage.objects.create(
            conversation=conversation,
            is_user=False,
            content=ai_response,
            message_type='voice',
            audio_file=audio_url
        )
    else:
        ai_response = ai_service.generate_text_response(content, history)
        
        ai_message = AIMessage.objects.create(
            conversation=conversation,
            is_user=False,
            content=ai_response,
            message_type='text'
        )
    
    return JsonResponse({
        'success': True,
        'ai_response': ai_response,
        'timestamp': ai_message.created_at.isoformat(),
        'message_id': str(ai_message.id)
    })


@login_required
@require_http_methods(["POST"])
def check_boredom(request):
    """Check if message indicates boredom and suggest AI chat"""
    data = json.loads(request.body)
    message = data.get('message', '')
    
    is_bored, suggestion = ai_service.handle_boredom_detection(message)
    
    if is_bored:
        return JsonResponse({
            'is_bored': True,
            'suggestion': suggestion
        })
    
    return JsonResponse({'is_bored': False})



