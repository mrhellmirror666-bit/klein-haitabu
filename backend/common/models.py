from django.db import models


def get_default_group_id():
    group, _ = Group.objects.get_or_create(slug="klein_haitabu", defaults={"name": "Klein Haitabu"})
    return group.pk


class Group(models.Model):
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
