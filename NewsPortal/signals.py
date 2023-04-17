from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.template.loader import render_to_string
from .tasks import send_notif
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Post


from .models import PostCategory


def send_notifications(preview, pk, title, subscribers):
    html_content = render_to_string(
        'post_created_email.html',
        {
            'text': preview,
            'link': f'{settings.SITE_URL}/news/{pk}',
        }
    )

    msg = EmailMultiAlternatives(
        subject=title,
        body='',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=subscribers,
    )

    msg.attach_alternative(html_content, 'text/html')
    msg.send()


@receiver(m2m_changed, sender=PostCategory)
def notify_about_new_post(sender, instance, **kwargs):
    if kwargs['action'] == 'post_add':
        categories = instance.category.all()
        subscribes_emails = []

        for category in categories:
            subscribes = category.subscribers.all()
            subscribes_emails += [s.email for s in subscribes]

        send_notifications(instance.text, instance.pk, instance.title, subscribes_emails)


@receiver(post_save, sender=Post)
def notify_client_post(sender, instance, created, **kwargs):
    send_notif.delay()