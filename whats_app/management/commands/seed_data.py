import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import make_password
import uuid

from whats_app.models import (
    User, Contact, Chat, ChatParticipant, Group, GroupAdmin,
    Message, MessageStatus, Status, StatusView, Channel, 
    ChannelFollower, ChannelPost, AIAssistant, AIConversation, AIMessage
)

# Kenyan phone numbers
KENYAN_PHONES = [
    '+254712345678', '+254723456789', '+254734567890', '+254745678901',
    '+254756789012', '+254767890123', '+254778901234', '+254789012345',
    '+254701234567', '+254722334455', '+254733445566', '+254744556677',
]

# Kenyan names
KENYAN_NAMES = [
    'Wanjiku', 'Kamau', 'Otieno', 'Akinyi', 'Mwangi', 'Njeri',
    'Omondi', 'Chebet', 'Kipchoge', 'Wambui', 'Karanja', 'Mumbua',
    'Kimani', 'Nyambura', 'Ondiek', 'Moraa', 'Kibet', 'Wairimu'
]

# Sheng and Kenyan slang messages
SHENG_MESSAGES = [
    "Niaje buda, uko poa?",
    "Maze niko fiti sana leo",
    "Tukutane CBD kesho",
    "Enyewe hii story ni noma",
    "Boss unanitreat lunch ama?",
    "Niko kwa ndai nikam",
    "Kijana nimeamua kumove",
    "Nilikuwa down lakini sasa niko top",
    "Umeskia story ya huyo jamaa?",
    "Ebu niambie vile ilikuwa",
    "Niko job saa hii, nitakucall baadaye",
    "Maze nimetrip na huyo dem",
    "Uko na dos ya kunichangia?",
    "Nimeamua kukata miti",
    "Hiyo movie ni fiti manze",
    "Tucheze ball kesho?",
    "Niko kwa plot tuone match",
    "Maze nimechoka na hii traffic",
    "Uko wapi? Niko hapo tu karibu",
    "Nisaidie na change ya matatu",
    "Hii jua inachoma sana leo",
    "Nimeona huyo msee pale tao",
    "Tukule nyama choma leo",
    "Enyewe Nairobi ni shida",
    "Nimebaki na thau moja tu",
    "Boss nipatiane hizi notes",
    "Maze hiyo dame ni mrembo sana",
    "Nisaidie kutext huyo mdem",
    "Niko ndani ya mat niaje",
    "Tutafika saa ngapi?",
]

# Sweet/romantic messages
SWEET_MESSAGES = [
    "Good morning baby, have a blessed day ❤️",
    "I miss you so much my love",
    "Thinking about you right now 💕",
    "You make me so happy babe",
    "Can't wait to see you tonight 😘",
    "You're the best thing that happened to me",
    "I love you more than words can say",
    "Sweet dreams my love 💤",
    "You light up my world ✨",
    "Missing your smile right now",
    "Babe when are we meeting?",
    "You're always on my mind 💭",
    "I'm so lucky to have you",
    "Thanks for being amazing ❤️",
    "Can't stop thinking about you",
    "You're my everything baby",
    "Love you to the moon and back 🌙",
    "My day is better with you in it",
    "You're my happy place 😊",
    "Forever and always ♾️",
]

# Casual messages
CASUAL_MESSAGES = [
    "Hey, how are you?",
    "What's up?",
    "Are you free tonight?",
    "Did you see that?",
    "Lol that's hilarious 😂",
    "I'm on my way",
    "Running a bit late",
    "Sorry, I was busy",
    "Call me when you're free",
    "Thanks so much!",
    "No problem",
    "Sure, sounds good",
    "Let me know",
    "Okay cool",
    "See you soon",
    "Take care",
    "Alright then",
    "Got it, thanks",
    "Will do",
    "Perfect timing",
]

# Group messages
GROUP_MESSAGES = [
    "Guys tupatane wapi?",
    "Saa ngapi tunakutana?",
    "Nani anakam na gari?",
    "Mko wapi sasa?",
    "Contribution ni ngapi?",
    "Weka pesa kwa group",
    "Meeting is at 3pm",
    "Don't be late guys",
    "Kila mtu alipe share yake",
    "Admin add Peter kwa group",
    "Guys tumefika",
    "Nani hajafika bado?",
    "Check the location I sent",
    "Bring your ID",
    "Dress code ni smart casual",
]

# Status messages
STATUS_TEXTS = [
    "Living my best life! ✨",
    "Grateful for another day 🙏",
    "Weekend vibes 🎉",
    "God is good all the time",
    "Hustle mode activated 💪",
    "Blessed and highly favored",
    "Making moves in silence",
    "Trust the process",
    "New week, new opportunities",
    "Positive vibes only ✌️",
]

# Channel post content
CHANNEL_POSTS = [
    "Breaking: New regulations announced by CBK",
    "Weather update: Heavy rains expected this weekend",
    "Traffic alert: Thika Road heavily congested",
    "Reminder: Deadline for tax returns is next week",
    "New restaurant opening in Westlands this Friday",
    "Job opportunity: Software developer position available",
    "Event: Music festival at KICC on Saturday",
    "Health tip: Stay hydrated during this hot weather",
    "Sports: Gor Mahia wins 2-0 against AFC Leopards",
    "Tech news: New smartphone launches in Kenya",
]

# Conversation templates
CONVERSATIONS = [
    [
        "Niaje, uko poa?",
        "Niko fiti boss, wewe je?",
        "Poa sana. Tukutane leo?",
        "Sawa, saa ngapi?",
        "Saa nne CBD?",
        "Perfect, tutaonana hapo"
    ],
    [
        "Babe I miss you",
        "I miss you too my love ❤️",
        "When can I see you?",
        "Come over tonight?",
        "Yes! I'll be there at 7",
        "Can't wait 😘"
    ],
    [
        "Hey, are you coming for the meeting?",
        "Yeah, what time again?",
        "3pm at the office",
        "Okay cool, see you there",
        "Don't forget the documents",
        "Got them, thanks"
    ],
    [
        "Maze umeskia?",
        "Umeskia nini?",
        "Story ya John",
        "Aah hapana, ni nini?",
        "Nitakushow tukikutana",
        "Eeh sawa basi"
    ],
    [
        "Good morning love",
        "Morning baby, how did you sleep?",
        "Like a baby, dreamt of you",
        "Aww you're so sweet ❤️",
        "Have a great day at work",
        "You too babe, love you"
    ]
]


class Command(BaseCommand):
    help = 'Seeds the database with realistic Kenyan WhatsApp data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=12,
            help='Number of users to create'
        )

    def handle(self, *args, **options):
        num_users = options['users']
        
        self.stdout.write('🚀 Starting to seed Kenyan WhatsApp data...\n')
        
        # Clear existing data (optional)
        self.stdout.write('🗑️  Clearing existing data...')
        self.clear_data()
        
        # Create users
        self.stdout.write('👥 Creating users...')
        users = self.create_users(num_users)
        
        # Create contacts
        self.stdout.write('📞 Creating contacts...')
        self.create_contacts(users)
        
        # Create private chats with conversations
        self.stdout.write('💬 Creating private chats...')
        self.create_private_chats(users)
        
        # Create groups
        self.stdout.write('👨‍👩‍👧‍👦 Creating groups...')
        self.create_groups(users)
        
        # Create statuses
        self.stdout.write('📸 Creating statuses...')
        self.create_statuses(users)
        
        # Create channels
        self.stdout.write('📢 Creating channels...')
        self.create_channels(users)
        
        # Create AI assistant
        self.stdout.write('🤖 Creating AI assistant...')
        self.create_ai_assistant(users)
        
        self.stdout.write(self.style.SUCCESS('\n✅ Database seeded successfully!'))
        self.stdout.write(f'Created {len(users)} users with realistic Kenyan data\n')

    def clear_data(self):
        """Clear existing data"""
        User.objects.all().delete()
        Chat.objects.all().delete()
        Status.objects.all().delete()
        Channel.objects.all().delete()
        AIAssistant.objects.all().delete()

    def create_users(self, num_users):
        """Create users with Kenyan phone numbers"""
        users = []
        for i in range(num_users):
            user = User.objects.create(
                username=f'user_{i+1}',
                phone_number=KENYAN_PHONES[i] if i < len(KENYAN_PHONES) else f'+2547{random.randint(10000000, 99999999)}',
                password=make_password('password123'),
                about=random.choice([
                    "Hey there! I'm using WhatsApp",
                    "Living my best life",
                    "Blessed and highly favored",
                    "Hustler 💪",
                    "God above everything 🙏",
                    "Available",
                    "Busy"
                ]),
                is_online=random.choice([True, False]),
                last_seen=timezone.now() - timedelta(minutes=random.randint(1, 120)),
                read_receipts=random.choice([True, False]),
                theme=random.choice(['light', 'dark']),
                font_size=random.choice(['small', 'medium', 'large'])
            )
            users.append(user)
        return users

    def create_contacts(self, users):
        """Create contacts between users"""
        for user in users:
            # Each user has 5-10 random contacts
            num_contacts = random.randint(5, min(10, len(users)-1))
            contacts = random.sample([u for u in users if u != user], num_contacts)
            
            for contact_user in contacts:
                Contact.objects.create(
                    user=user,
                    contact_user=contact_user,
                    name=random.choice(KENYAN_NAMES),
                    is_favorite=random.choice([True, False, False, False]),
                    is_blocked=False
                )

    def create_private_chats(self, users):
        """Create private chats with realistic conversations"""
        created_pairs = set()
        
        for _ in range(len(users) * 2):
            user1, user2 = random.sample(users, 2)
            pair = tuple(sorted([user1.id, user2.id]))
            
            if pair in created_pairs:
                continue
            created_pairs.add(pair)
            
            # Create chat
            chat = Chat.objects.create(chat_type='private')
            
            # Add participants
            ChatParticipant.objects.create(
                chat=chat,
                user=user1,
                is_pinned=random.choice([True, False, False]),
                is_muted=random.choice([True, False, False, False])
            )
            ChatParticipant.objects.create(
                chat=chat,
                user=user2,
                is_pinned=random.choice([True, False, False]),
                is_muted=random.choice([True, False, False, False])
            )
            
            # Add a conversation
            if random.random() > 0.3:
                self.add_conversation(chat, user1, user2)

    def add_conversation(self, chat, user1, user2):
        """Add a realistic conversation to a chat"""
        # Choose conversation type
        if random.random() > 0.5:
            # Use a template conversation
            messages = random.choice(CONVERSATIONS)
            users = [user1, user2]
            
            for i, msg_text in enumerate(messages):
                sender = users[i % 2]
                receiver = users[(i + 1) % 2]
                
                msg = Message.objects.create(
                    chat=chat,
                    sender=sender,
                    message_type='text',
                    content=msg_text,
                    created_at=timezone.now() - timedelta(hours=random.randint(1, 48))
                )
                
                # Create message status only for receiver (not sender)
                # Use get_or_create to avoid duplicates
                MessageStatus.objects.get_or_create(
                    message=msg,
                    user=receiver,
                    defaults={'status': random.choice(['delivered', 'read'])}
                )
        else:
            # Random messages
            num_messages = random.randint(3, 10)
            message_pool = SHENG_MESSAGES + SWEET_MESSAGES + CASUAL_MESSAGES
            
            for i in range(num_messages):
                sender = random.choice([user1, user2])
                receiver = user2 if sender == user1 else user1
                
                msg = Message.objects.create(
                    chat=chat,
                    sender=sender,
                    message_type='text',
                    content=random.choice(message_pool),
                    created_at=timezone.now() - timedelta(hours=random.randint(1, 72))
                )
                
                # Create message status only for receiver
                # Use get_or_create to avoid duplicates
                MessageStatus.objects.get_or_create(
                    message=msg,
                    user=receiver,
                    defaults={'status': random.choice(['sent', 'delivered', 'read'])}
                )

    def create_groups(self, users):
        """Create WhatsApp groups"""
        group_names = [
            'Family Matters',
            'Chama Members',
            'Weekend Plans',
            'Work Team',
            'School Reunion',
            'Boda Boda Sacco',
            'Prayer Warriors 🙏',
            'Nairobi Connects',
            'Business Network',
            'Football Fans'
        ]
        
        for group_name in random.sample(group_names, 5):
            # Create chat
            chat = Chat.objects.create(chat_type='group')
            
            # Create group
            creator = random.choice(users)
            group = Group.objects.create(
                chat=chat,
                name=group_name,
                description=f'Welcome to {group_name}',
                created_by=creator,
                only_admins_can_send=random.choice([True, False, False]),
            )
            
            # Add creator as admin
            GroupAdmin.objects.create(group=group, user=creator)
            
            # Add members (5-10 people)
            members = random.sample(users, random.randint(5, min(10, len(users))))
            for member in members:
                ChatParticipant.objects.create(
                    chat=chat,
                    user=member,
                    is_muted=random.choice([True, False, False, False])
                )
            
            # Add group messages
            for _ in range(random.randint(5, 15)):
                sender = random.choice(members)
                msg = Message.objects.create(
                    chat=chat,
                    sender=sender,
                    message_type='text',
                    content=random.choice(GROUP_MESSAGES + CASUAL_MESSAGES),
                    created_at=timezone.now() - timedelta(hours=random.randint(1, 168))
                )
                
                # Create message status for all members except sender
                # Use get_or_create to avoid duplicates
                for member in members:
                    if member != sender:
                        MessageStatus.objects.get_or_create(
                            message=msg,
                            user=member,
                            defaults={'status': random.choice(['sent', 'delivered', 'read'])}
                        )

    def create_statuses(self, users):
        """Create WhatsApp statuses"""
        for user in random.sample(users, min(8, len(users))):
            # Create 1-3 statuses per user
            for _ in range(random.randint(1, 3)):
                status = Status.objects.create(
                    user=user,
                    status_type='text',
                    content=random.choice(STATUS_TEXTS),
                    background_color=random.choice(['#000000', '#FF0000', '#00FF00', '#0000FF', '#FF00FF']),
                    created_at=timezone.now() - timedelta(hours=random.randint(1, 20)),
                    expires_at=timezone.now() + timedelta(hours=random.randint(4, 24))
                )
                
                # Add views from other users
                viewers = random.sample([u for u in users if u != user], random.randint(2, 6))
                for viewer in viewers:
                    StatusView.objects.create(status=status, viewer=viewer)

    def create_channels(self, users):
        """Create WhatsApp channels"""
        channel_names = [
            'Nairobi News',
            'Tech Kenya',
            'Daily Motivation',
            'Job Opportunities',
            'Sports Updates',
        ]
        
        for channel_name in channel_names:
            creator = random.choice(users)
            channel = Channel.objects.create(
                name=channel_name,
                description=f'Official {channel_name} channel',
                created_by=creator,
                verified=random.choice([True, False])
            )
            
            # Add followers
            followers = random.sample(users, random.randint(5, len(users)))
            for follower in followers:
                ChannelFollower.objects.create(
                    channel=channel,
                    user=follower,
                    is_muted=random.choice([True, False, False])
                )
            
            # Add posts
            for _ in range(random.randint(3, 8)):
                ChannelPost.objects.create(
                    channel=channel,
                    content=random.choice(CHANNEL_POSTS),
                    post_type='text',
                    created_at=timezone.now() - timedelta(hours=random.randint(1, 168))
                )

    def create_ai_assistant(self, users):
        """Create AI assistant and conversations"""
        assistant = AIAssistant.objects.create(
            name="WhatsApp AI",
            is_active=True
        )
        
        # Create conversations for some users
        for user in random.sample(users, min(4, len(users))):
            conversation = AIConversation.objects.create(
                user=user,
                assistant=assistant
            )
            
            # Add some messages
            ai_responses = [
                "Hello! How can I help you today?",
                "I'm here to assist you with anything you need.",
                "That's a great question! Let me help you with that.",
                "Sure, I can help you with that.",
                "Is there anything else I can help you with?",
            ]
            
            for i in range(random.randint(2, 6)):
                # User message
                AIMessage.objects.create(
                    conversation=conversation,
                    is_user=True,
                    content=random.choice(CASUAL_MESSAGES),
                    created_at=timezone.now() - timedelta(minutes=random.randint(5, 60))
                )
                
                # AI response
                AIMessage.objects.create(
                    conversation=conversation,
                    is_user=False,
                    content=random.choice(ai_responses),
                    created_at=timezone.now() - timedelta(minutes=random.randint(4, 59))
                )