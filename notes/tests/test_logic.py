"""
Тесты проверяют функциональность создания, редактирования и удаления заметок.

Тестируются следующие аспекты:
- Возможность создания заметки авторизованным пользователем.
- Проверка уникальности слага при создании заметки.
- Автоматическое создание уникального слага, если он не указан.
- Возможность удаления и редактирования заметки только автором.
"""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from http import HTTPStatus
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note


User = get_user_model()


class TestNoteCreation(TestCase):
    """Тестирование создания заметки."""

    NOTE_TITLE = 'Название заметки'
    NOTE_TEXT = 'Просто текст заметки.'

    @classmethod
    def setUpTestData(cls):
        """Настройка данных для тестов."""
        cls.add_url = reverse('notes:add')
        cls.success_url = reverse('notes:success')
        cls.login_url = reverse('users:login')

        cls.form_data = {
            'title': cls.NOTE_TITLE, 'text': cls.NOTE_TEXT}

        cls.user = User.objects.create(username='testUserAuthor')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        
    def test_anonymous_user_cant_create_note(self):
        """Проверяет, что анонимный пользователь не может создать заметку."""
        response = self.client.post(self.add_url, data=self.form_data)
        expected_url = f'{self.login_url}?next={self.add_url}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), 0)

    def test_user_can_create_note(self):
        """Проверяем, что авторизованный пользователь может создать заметку."""
        response = self.auth_client.post(self.add_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)

        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

        note_obj = Note.objects.first()
        self.assertEqual(note_obj.title, self.NOTE_TITLE)
        self.assertEqual(note_obj.text, self.NOTE_TEXT)
        self.assertEqual(note_obj.author, self.user)

    def test_not_unique_slug(self):
        """Проверяем, что создать заметку можно только с уникальным слагом."""
        # Создаём заметку:
        self.note = Note.objects.create(
            title='Тестовая заметка',
            text='Текст заметки',
            author=self.user,
            slug='testnote'
        )
        # Используем существующий слаг:
        self.form_data['slug'] = self.note.slug
        response = self.auth_client.post(self.add_url, data=self.form_data)
        self.assertFormError(
            response.context['form'],
            'slug',
            errors=(self.note.slug + WARNING)
        )
        # Убеждаемся, что новая заметка не была создана:
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        """Заметка получает уникальный слаг, если он не указан."""
        response = self.auth_client.post(self.add_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        # Убеждаемся, что заметка создана:
        self.assertEqual(Note.objects.count(), 1)
        expected_slug = slugify(self.form_data['title'])
        # Получаем созданную заметку:
        new_note = Note.objects.get()
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(TestCase):
    """Тестирование редактирования и удаления заметок."""

    NOTE_TEXT = 'Просто текст заметки.'
    NEW_NOTE_TEXT = 'Полностью новый текст заметки.'

    @classmethod
    def setUpTestData(cls):
        """Настройка данных для тестов."""
        cls.author = User.objects.create(username='testUserAuthor')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        # Создаём и логиним пользователя, который не является автором заметки
        cls.other_user = User.objects.create(username='testUserNonAuthor')
        cls.other_user_client = Client()
        cls.other_user_client.force_login(cls.other_user)

        cls.note = Note.objects.create(
            # Слаг создаётся автоматически через метод модели.
            title='Название заметки', text=cls.NOTE_TEXT, author=cls.author
        )

        # Создаём все нужные url.
        slug = (cls.note.slug,)
        cls.success_url = reverse('notes:success')
        cls.delete_url = reverse(
            'notes:delete', args=slug
        )
        cls.edit_url = reverse(
            'notes:edit', args=slug
        )
        cls.form_data = {
            'title': cls.note.title,
            'text': cls.NEW_NOTE_TEXT
        }

    def test_author_can_delete_note(self):
        """Проверка, что автор может удалить свою заметку."""
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # Проверяем, что комментарий удалён.
        self.assertEqual(Note.objects.count(), 0)

    def test_user_cant_delete_note_of_another_user(self):
        """Пользователь не может удалить заметку другого пользователя."""
        response = self.other_user_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что заметка не удалена:
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        """Проверка, что автор может редактировать свою заметку."""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        # Проверяем, что текст комментария соответствует обновленному.
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_user_cant_edit_note_of_another_user(self):
        """Пользователь не может редактировать заметку другого пользователя."""
        response = self.other_user_client.post(
            self.edit_url, data=self.form_data
        )
        # В QS только заметки other_user.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        # Проверяем, что текст не изменился
        self.assertEqual(self.note.text, self.NOTE_TEXT)
