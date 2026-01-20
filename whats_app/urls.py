# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('', views.login_page, name='login'),
    path('register/', views.register, name='register'),
    path('qr-login/', views.qr_login, name='qr_login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Main chat interface
    path('chat/', views.chat_home, name='chat_home'),
    path('chat/<uuid:chat_id>/', views.chat_view, name='chat_view'),
    path('new-chat/', views.new_chat, name='new_chat'),
    
    # Message actions
    path('api/send-message/', views.send_message, name='send_message'),
    path('api/delete-message/', views.delete_message, name='delete_message'),
    path('api/edit-message/', views.edit_message, name='edit_message'),
    
    # Group management
    path('create-group/', views.create_group, name='create_group'),
    
    # User actions
    path('api/block-user/', views.block_user, name='block_user'),
    path('api/pin-chat/', views.pin_chat, name='pin_chat'),
    path('api/archive-chat/', views.archive_chat, name='archive_chat'),
    
    # Settings
    path('settings/', views.settings_view, name='settings'),
    
    # Status
    path('status/', views.status_view, name='status'),
    path('api/create-status/', views.create_status, name='create_status'),
    
    # AI Assistant
    path('ai-chat/', views.ai_chat, name='ai_chat'),
    path('api/send-ai-message/', views.send_ai_message, name='send_ai_message'),
]

