"""Проверка списка заметок и детальной информации о заметке."""


from django.test import Client, TestCase
from django.urls import reverse

from django.contrib.auth import get_user_model

from notes.models import Note


User = get_user_model()


class TestNoteList(TestCase):
    """Тест для проверки отображения списка заметок."""

    @classmethod
    def setUpTestData(cls):
        """
        Создаёт тестовые данные для всех тестов в классе.

        Создаётся пользователь и несколько заметок для тестирования.
        """
        cls.author = User.objects.create(username='Автор заметки')
        Note.objects.bulk_create(
            Note(
                title=f'Заметка {index}',
                text='Просто текст.',
                author=cls.author,
                slug=f'note-{index}'
                )
            for index in range(3)
        )

    def test_notes_order(self):
        """
        Проверяет, что заметки в списке выводятся в порядке их создания.

        С помощью сравнения pk убеждаемся, что каждый последующий объект имеет
        больший pk.
        """
        self.client.force_login(self.author)
        url = reverse('notes:list')
        self.client.get(url)
        notes = list(Note.objects.all())
        for i in range(1, len(notes)):
            self.assertTrue(notes[i - 1].pk < notes[i].pk)


class TestNoteDetail(TestCase):
    """
    Тест для проверки детальной информации о заметке.

    Проверяет наличие ожидаемых полей в контексте ответа.
    """

    @classmethod
    def setUpTestData(cls):
        """
        Создаёт тестовые данные для всех тестов в классе.

        Создаётся пользователь и заметка для тестирования.
        """
        cls.author = User.objects.create(username='author')
        cls.note = Note.objects.create(
            pk=1,
            title='Тестовая заметка',
            text='Текст заметки',
            author=cls.author,
            slug='testnote'
        )
        cls.url = reverse('notes:detail', kwargs={'note_slug': cls.note.slug})
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.author)

    def test_note_detail_contains_expected_fields(self):
        """
        Проверяет, что детальная страница заметки содержит все ожидаемые поля.

        Поля включают id, title, text, slug и author.
        """
        response = self.auth_client.get(self.url)

        self.assertIn('note', response.context)
        note_obj = response.context['note']

        expected = (
            ('id', self.note.pk),
            ('title', self.note.title),
            ('text',   self.note.text),
            ('slug',   self.note.slug),
            ('author', self.author),
        )

        for field, exp_value in expected:
            with self.subTest(field=field):
                self.assertEqual(getattr(note_obj, field), exp_value)

    def test_note_detail_contains_edit_and_delete_href(self):
        """
        Проверяет наличие ссылки для редактирования и удаления заметки.

        Проверяются наличие href для редактирования и удаления с
        соответствующими маршрутами.
        """
        response = self.auth_client.get(self.url)

        self.assertIn('note', response.context)
        note_obj = response.context['note']

        slug = note_obj.slug

        route_names = (
            ('edit',   'notes:edit'),
            ('delete', 'notes:delete'),
        )

        for name, route in route_names:
            with self.subTest(link=name):
                url = reverse(route, kwargs={'note_slug': slug})
                self.assertContains(response, f'href="{url}"')
