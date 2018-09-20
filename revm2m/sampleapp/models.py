from django.db import models


class Blog(models.Model):
    name = models.CharField(max_length=100)


class Author(models.Model):
    name = models.CharField(max_length=200)
    joined = models.DateField()

    def __repr__(self):
        return self.name


class Entry(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE)
    headline = models.CharField(max_length=255)
    authors = models.ManyToManyField(Author)
    rating = models.IntegerField()

    def __repr__(self):
        return self.headline
