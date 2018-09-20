from collections import defaultdict

from django.db.models import Prefetch
from django.test import TestCase, override_settings

from revm2m.sampleapp.dbcount import d
from revm2m.sampleapp.models import Blog, Author, Entry
from datetime import date
from django.db import connection


class ReverseM2MTest(TestCase):
    def setUp(self):
        d('>setup')
        b = Blog.objects.create(name='myblog')
        self.a1 = Author.objects.create(name='author1', joined=date(2017,1,1))
        self.a2 = Author.objects.create(name='author2', joined=date(2018,1,1))
        self.a3 = Author.objects.create(name='author3', joined=date(2018,2,1))
        for i in range(4, 100):
            # authors without entries.
            Author.objects.create(name='author%d' % i, joined=date(2018,2,1))

        self.entry1 = Entry.objects.create(blog=b, headline='entry1', rating=1)
        self.entry1.authors.set([self.a1, self.a2, self.a3])

        self.entry2 = Entry.objects.create(blog=b, headline='entry2', rating=2)
        self.entry2.authors.set([self.a1, self.a2, self.a3])

        self.entry3 = Entry.objects.create(blog=b, headline='entry3', rating=3)
        self.entry3.authors.set([self.a1, self.a2, self.a3])
        self.entry4 = Entry.objects.create(blog=b, headline='entry4', rating=4)
        self.entry4.authors.set([self.a1, self.a3])
        self.entry5 = Entry.objects.create(blog=b, headline='entry5', rating=5)
        self.entry5.authors.set([self.a1, self.a2])
        self.entry5.save()
        d('<setup')

    @override_settings(DEBUG=True)
    def test_rev_m2m_1(self):
        d('>test-rev-m2m-1')
        res = {}
        authors = Author.objects.filter(joined__year=date.today().year)

        for author in authors:
            res[author] = set(author.entry_set.filter(rating__gte=4))

        self.assertEqual(len(res), len(authors))

        self.assertEqual(res[self.a2], {self.entry5})
        self.assertEqual(res[self.a3], {self.entry4})

        dbcount = d('<test-rev-m2m-1')
        self.assertLess(dbcount, 4)  # 99

    @override_settings(DEBUG=True)
    def test_rev_m2m_2(self):
        d('>test-rev-m2m-2')
        res = {}
        authors = Author.objects.filter(joined__year=date.today().year)
        entries = Entry.objects.select_related().filter(rating__gte=4, authors__in=authors)

        for author in authors:
            res[author] = {e for e in entries if e.authors.filter(pk=author.pk)}

        self.assertEqual(len(res), len(authors))

        self.assertEqual(res[self.a2], {self.entry5})
        self.assertEqual(res[self.a3], {self.entry4})
        dbcount = d('<test-rev-m2m-2')
        self.assertLess(dbcount, 4)  # 198

    @override_settings(DEBUG=True)
    def test_rev_m2m_3(self):
        d('>test-rev-m2m-3')
        res = {}
        _authors = Author.objects.filter(joined__year=date.today().year)
        _entries = Entry.objects.select_related().filter(rating__gte=4, authors__in=_authors)
        authors = {a.id: a for a in _authors}
        entries = {e.id: e for e in _entries}
        c = connection.cursor()
        c.execute("""
            select entry_id, author_id 
            from sampleapp_entry_authors
            where author_id in (%s)
        """ % ','.join(str(v) for v in authors.keys()))

        res = {a: set() for a in _authors}
        for eid, aid in c.fetchall():
            if eid in entries:
                res[authors[aid]].add(entries[eid])

        self.assertEqual(len(res), len(authors))

        self.assertEqual(res[self.a2], {self.entry5})
        self.assertEqual(res[self.a3], {self.entry4})
        dbcount = d('<test-rev-m2m-3', show=True, total=True)
        self.assertLess(dbcount, 4)  # 3

    @override_settings(DEBUG=True)
    def test_rev_m2m_4(self):
        d('>test-rev-m2m-4')
        res = {}
        authors = Author.objects.filter(joined__year=date.today().year)
        entries = Entry.objects.prefetch_related('authors').filter(rating__gte=4, authors__in=authors)

        for author in authors:
            res[author] = {e for e in entries if e.authors.filter(pk=author.pk)}

        self.assertEqual(len(res), len(authors))

        self.assertEqual(res[self.a2], {self.entry5})
        self.assertEqual(res[self.a3], {self.entry4})
        dbcount = d('<test-rev-m2m-4')
        self.assertLess(dbcount, 4)  # 198

    @override_settings(DEBUG=True)
    def test_rev_m2m_6(self):
        d('>test-rev-m2m-6')
        res = {}
        authors = Author.objects.prefetch_related('entry_set').filter(joined__year=date.today().year)

        for author in authors:
            res[author] = set(author.entry_set.filter(rating__gte=4))

        self.assertEqual(len(res), len(authors))

        self.assertEqual(res[self.a2], {self.entry5})
        self.assertEqual(res[self.a3], {self.entry4})

        dbcount = d('<test-rev-m2m-6')
        self.assertLess(dbcount, 4)  # 99

    @override_settings(DEBUG=True)
    def test_rev_m2m_wvo(self):
        d('>test-rev-m2m-wvo')
        res = {}
        good_ratings = Prefetch(
            'entry_set',
            queryset=Entry.objects.filter(rating__gte=4),
            to_attr = 'good_ratings'
        )

        authors = Author.objects.filter(
            joined__year=date.today().year
        ).prefetch_related(
            good_ratings
        )
        res = {
            author: set(author.good_ratings)
            for author in authors
        }
        print(res)

        self.assertEqual(len(res), len(authors))

        self.assertEqual(res[self.a2], {self.entry5})
        self.assertEqual(res[self.a3], {self.entry4})

        dbcount = d('<test-rev-m2m-wvo')
        self.assertLess(dbcount, 4)  # 99
