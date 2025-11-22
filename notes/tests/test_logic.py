"""Тестирование логики приложения."""


from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestNoteCreation(TestCase):
    """Тестирование создания заметки."""

    NOTE_TITLE = 'Название заметки'
    NOTE_TEXT = 'Просто текст заметки.'

    @classmethod
    def setUpTestData(cls):
        """Настройка данных для тестов."""
        cls.url = reverse('notes:add')
        cls.success_url = reverse('notes:success')
        cls.form_data = {
            'title': cls.NOTE_TITLE, 'text': cls.NOTE_TEXT}
        cls.user = User.objects.create(username='testUserAuthor')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

    def test_anonymous_user_cant_create_note(self):
        """Проверка, что анонимный пользователь не может создать заметку."""
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        """Проверка, что авторизованный пользователь может создать заметку."""
        response = self.auth_client.post(self.url, data=self.form_data)
        # Проверяем, что редирект привёл на страницу успешного выполнения
        # операции.
        self.assertRedirects(response, self.success_url)

        notes_count = Note.objects.count()
        # Убеждаемся, что есть одна заметка.
        self.assertEqual(notes_count, 1)

        note_obj = Note.objects.first()

        self.assertEqual(note_obj.title, self.NOTE_TITLE)
        self.assertEqual(note_obj.text, self.NOTE_TEXT)
        self.assertEqual(note_obj.author, self.user)


class TestNoteEditDelete(TestCase):
    """Тестирование редактирования и удаления заметок."""

    NOTE_TEXT = 'Просто текст заметки.'
    NEW_NOTE_TEXT = 'Полностью новый текст заметки.'

    @classmethod
    def setUpTestData(cls):
        """Настройка данных для тестов."""
        # Создаём и логиним автора заметки.
        cls.author = User.objects.create(username='testUserAuthor')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        # Создаём и логиним пользователя, который не является автором заметки
        cls.non_author = User.objects.create(username='testUserNonAuthor')
        cls.non_author_client = Client()
        cls.non_author_client.force_login(cls.non_author)

        # Создаём заметку.
        cls.note = Note.objects.create(
            # Слаг создаётся автоматически через метод модели.
            title='Название заметки', text=cls.NOTE_TEXT, author=cls.author
        )

        # Создаём все нужные url.
        cls.success_url = reverse('notes:success')
        cls.delete_url = reverse(
            'notes:delete', kwargs={'note_slug': cls.note.slug}
        )
        cls.edit_url = reverse(
            'notes:edit', kwargs={'note_slug': cls.note.slug}
        )
        cls.form_data = {
            'title': cls.note.title,
            'text': cls.NEW_NOTE_TEXT
        }

    def test_author_can_delete_note(self):
        """Проверка, что автор может удалить свою заметку."""
        response = self.author_client.delete(self.delete_url)
        # Проверяем, что редирект привёл на страницу успешного выполнения
        # операции.
        self.assertRedirects(response, self.success_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        # Считаем количество комментариев в системе.
        notes_count = Note.objects.count()
        # Проверяем, что комментарий удалён.
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        """Пользователь не может удалить заметку другого пользователя."""
        # Выполняем запрос на удаление
        response = self.non_author_client.delete(self.delete_url)
        # Проверяем, что вернулась 404 ошибка.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        # Убедимся, что заметка не удалена.
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        """Проверка, что автор может редактировать свою заметку."""
        # Выполняем запрос на редактирование от имени автора комментария.
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        # Обновляем объект заметки.
        self.note.refresh_from_db()
        # Проверяем, что текст комментария соответствует обновленному.
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)

    def test_user_cant_edit_note_of_another_user(self):
        """Пользователь не может редактировать заметку другого пользователя."""
        response = self.non_author_client.post(
            self.edit_url, data=self.form_data
        )
        # В QS только заметки non_author пользователя, других он не
        # получает -> 404.
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NOTE_TEXT)
