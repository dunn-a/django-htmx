# Generated by Django 5.0.4 on 2024-04-16 14:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("a_posts", "0010_likedpost_post_like"),
    ]

    operations = [
        migrations.RenameField(
            model_name="post",
            old_name="like",
            new_name="likes",
        ),
    ]