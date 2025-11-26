"""Тесты для списка заметок."""


from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus

from django.contrib.auth import get_user_model

from notes.forms import NoteForm
from notes.models import Note


User = get_user_model()


class TestNoteList(TestCase):
    """Тест для проверки отображения списка заметок."""

    @classmethod
    def setUpTestData(cls):
        """
        Создаёт тестовые данные для всех тестов в классе.

        Создаётся пользователь и заметка для тестирования.
        """
        cls.author = User.objects.create(username='author')
        cls.other_user = User.objects.create(username='not_author')
        cls.note = Note.objects.create(
            title='Тестовая заметка',
            text='Текст заметки',
            author=cls.author,
            slug='testnote-1'
        )
        cls.other_user_note = Note.objects.create(
            title='Тестовая заметка',
            text='Текст заметки',
            author=cls.other_user,
            slug='testnote-2'
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.other_user_client = Client()
        cls.other_user_client.force_login(cls.other_user)

        cls.url = reverse('notes:list')

    def test_list_page_contains_note(self):
        response = self.author_client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn(self.note, response.context['object_list'])

    def test_list_page_contains_only_author_notes(self):
        """Список заметок не содержит заметки другого пользователя."""
        response = self.author_client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        object_list = response.context['object_list']
        self.assertIn(self.note, object_list)
        self.assertNotIn(self.other_user_note, object_list)

    def test_add_and_edit_pages_contain_form(self):
        urls = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        )
        for name, args in urls:
            url = reverse(name, args=args)
            response = self.author_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertIn('form', response.context)
            note_form = response.context['form']
            # Проверяем, что форма - экземпляр класса NoteForm:
            self.assertIsInstance(note_form, NoteForm)
