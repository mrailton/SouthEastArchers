from django.db import models
from django.conf import settings


class News(models.Model):
    """News articles published by admins"""

    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='news_posts'
    )
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'news_news'
        ordering = ['-created_at']
        verbose_name = 'News'
        verbose_name_plural = 'News'

    def __str__(self):
        return self.title
