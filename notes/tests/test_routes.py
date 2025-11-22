"""
Модуль содержит тесты для проверки доступности маршрутов в приложении.

Тестируются следующие сценарии:
- доступность общедоступных страниц для неавторизованных пользователей;
- доступность заметок для их автора и недоступность для других пользователей;
- перенаправление неавторизованных пользователей на страницу логина при
    попытке доступа к защищенным маршрутам.
"""

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):
    """Тест для маршрутов."""

    NOTE_URLS = ('notes:detail', 'notes:edit', 'notes:delete')

    @classmethod
    def setUpTestData(cls):
        """Устанавливаем данные для теста.

        Метод вызывается один раз, перед выполнением всех тестов класса.
        """
        cls.author = User.objects.create(username='testUserAuthor')
        cls.non_author = User.objects.create(username='testUserAnonymous')
        cls.note = Note.objects.create(
            title='Название',
            text='Текст',
            author=cls.author,
        )

    def test_pages_availability(self):
        """Доступность страниц для неавторизованного пользователя."""
        urls = (
            ('notes:home'),
            ('users:signup'),
            ('users:login'),
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note_detail_edit_delete(self):
        """
        Доступность заметки для её автора и недоступность для анонима.

        Проверяется:
        - Автор может просматривать, редактировать и удалять свою заметку.
        - Пользователь, не являющийся автором заметки не имеет никакого
            доступа к заметке.

        Статусы:
        - HTTPStatus.OK для автора заметки.
        - HTTPStatus.NOT_FOUND для другого пользователя.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.non_author, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in self.NOTE_URLS:
                url = reverse(name, kwargs={'note_slug': self.note.slug})
                response = self.client.get(url)
                self.assertEqual(response.status_code, status)

    def test_redirect_for_anonymous_clien(self):
        """Проверка редиректов для неавторизованного пользователя.

        Анонимный пользователь перенаправляется на страницу логина при попытке
        доступа к любым url, связанным с заметкой, из константы NOTE_URLS.

        Для каждого URL из NOTE_URLS выполняется проверка, что клиент получает
        редирект на страницу логина с параметром next, содержащим исходный
        запрошенный URL.
        """
        login_url = reverse('users:login')
        for name in self.NOTE_URLS:
            with self.subTest(name=name):
                url = reverse(name, kwargs={'note_slug': self.note.slug})
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
