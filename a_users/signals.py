from django.dispatch import receiver
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from .models import Profile
from django.shortcuts import get_object_or_404

@receiver(post_save, sender=User)
def creat_profile(sender, instance, created:bool, **kwargs):
    user = instance
    if created:
        Profile.objects.create(
            user = user,
            email = user.email,
        )
        
    else:
        profile = get_object_or_404(Profile, user=user)
        if user.email != profile.email:
            profile.email = user.email
            profile.save()
        
        
        
@receiver(post_save, sender=Profile)
def update_user(sender, instance, created:bool, **kwargs):
    profile = instance
    if created == False:
        user = get_object_or_404(User, id=profile.user.id)
        if user.email != profile.email:
            user.email = profile.email
            user.save()