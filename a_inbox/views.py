from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from .models import *
from a_users.models import Profile
from .forms import InboxNewMessageForm
from django.db.models import Q
from cryptography.fernet import Fernet
from django.conf import settings

f = Fernet(settings.ENCRYPT_KEY)

@login_required
def inbox_view(request, conversation_id=None):
    my_conversations = Conversation.objects.filter(participants=request.user)
    if conversation_id:
        conversation = get_object_or_404(my_conversations, id=conversation_id)
        latest_message = conversation.messages.first()
        if conversation.is_seen == False and latest_message.sender != request.user:
            conversation.is_seen = True
            conversation.save()
    else:
        conversation = None
    context = {
        'conversation': conversation,
        "my_conversations": my_conversations
    }
    return render(request, "a_inbox/inbox.html", context)


def search_users(request):
    letters = request.GET.get('search_user')
    if request.htmx:
        if len(letters) > 0:
            profiles = Profile.objects.filter(realname__icontains=letters)
            p_uids = profiles.values_list('user', flat=True)
            users = User.objects.filter(
                Q(username__icontains=letters) | Q(id__in=p_uids)
            ).exclude(username=request.user.username)
            return render(request, 'a_inbox/list_searchuser.html', {'users': users})
        else:
            return HttpResponse('')
    else:
        raise Http404()
    
    
@login_required
def new_message(request, recipient_id):
    recipient = get_object_or_404(User, id=recipient_id)
    new_message_form = InboxNewMessageForm()
    
    if request.method == 'POST':
        form = InboxNewMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            
            #encrypt message
            message_original = form.cleaned_data['body']
            message_bytes = message_original.encode('utf-8')
            message_encrypted = f.encrypt(message_bytes)
            message_decoded = message_encrypted.decode('utf-8')
            message.body = message_decoded
            message.sender = request.user
            my_conversations = request.user.conversations.all()
            for old_conversation in my_conversations:
                if recipient in old_conversation.participants.all():
                    message.conversation = old_conversation
                    message.save()
                    old_conversation.lastmessage_created = timezone.now()
                    old_conversation.is_seen=False
                    old_conversation.save()
                    return redirect('inbox', old_conversation.id)
                    
            new_conversation = Conversation.objects.create()
            new_conversation.participants.add(request.user, recipient)
            new_conversation.save()
            message.conversation = new_conversation 
            message.save()
            return redirect('inbox', new_conversation.id)
            
    context = {
        'recipient': recipient,
        'new_message_form': new_message_form,
    }
    return render(request, 'a_inbox/form_newmessage.html', context)


@login_required
def new_reply(request, conversation_id):
    new_message_form = InboxNewMessageForm()
    my_conversations = request.user.conversations.all()
    conversation = get_object_or_404(my_conversations, id=conversation_id)
    context = {
        'new_message_form': new_message_form,
        'conversation': conversation,
    }
    
    if request.method == "POST":
        form = InboxNewMessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message_original = form.cleaned_data['body']
            message_bytes = message_original.encode('utf-8')
            message_encrypted = f.encrypt(message_bytes)
            message_decoded = message_encrypted.decode('utf-8')
            message.body = message_decoded
            message.sender = request.user
            message.conversation = conversation
            message.save()
            conversation.lastmessage_created = timezone.now()
            conversation.is_seen=False
            conversation.save()
            return redirect('inbox', conversation.id)
    
    return render(request, 'a_inbox/form_newreply.html', context)



def notify_newmessage(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    latest_message = conversation.messages.first()
    if conversation.is_seen == False and latest_message.sender != request.user:
        return render(request, 'a_inbox/notify_icon.html')
    else:
        return HttpResponse('')
    
    

def notify_inbox(request):
    my_conversations = Conversation.objects.filter(participants=request.user, is_seen=False)
    for conversation in my_conversations:
        latest_message = conversation.messages.first()
        if latest_message.sender != request.user:
            return render(request, 'a_inbox/notify_icon.html')
    return HttpResponse('')
    