import pytest
from pytest_django.asserts import assertFormError, assertRedirects

from django.urls import reverse
from http import HTTPStatus
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note


def test_user_can_create_note(author_client, author, form_data):
    url = reverse('notes:add')
    response = author_client.post(url, data=form_data)
    assertRedirects(response, reverse('notes:success'))
    assert Note.objects.count() == 1
    new_note = Note.objects.get()
    assert new_note.title == form_data['title']
    assert new_note.text == form_data['text']
    assert new_note.slug == form_data['slug']
    assert new_note.author == author


@pytest.mark.django_db
def test_anonymous_user_cant_create_note(client, form_data):
    url = reverse('notes:add')
    response = client.post(url, data=form_data)
    login_url = reverse('users:login')
    expected_url = f'{login_url}?next={url}'
    assertRedirects(response, expected_url)
    assert Note.objects.count() == 0


def test_not_unique_slug(author_client, note, form_data):
    """Создать заметку можно только с уникальным слагом."""
    url = reverse('notes:add')
    form_data['slug'] = note.slug
    response = author_client.post(url, data=form_data)
    # Проверяем, что в ответе содержится ошибка формы для поля slug:
    assertFormError(
        response.context['form'], 'slug', errors=(note.slug + WARNING)
    )
    # Убеждаемся, что новая заметка не была создана:
    assert Note.objects.count() == 1


# Фикстура author_client сама открывает транзакцию и
# обеспечивает доступ к базе данных, благодаря django.test.Client.
def test_empty_slug(author_client, form_data):
    """Заметка получает уникальный слаг, если он не указан."""
    url = reverse('notes:add')
    form_data.pop('slug')
    response = author_client.post(url, data=form_data)
    assertRedirects(response, reverse('notes:success'))
    assert Note.objects.count() == 1
    new_note = Note.objects.get()
    expected_slug = slugify(form_data['title'])
    assert new_note.slug == expected_slug


def test_author_can_edit_note(author_client, form_data, note, slug_for_args):
    url = reverse('notes:edit', args=slug_for_args)
    response = author_client.post(url, data=form_data)
    assertRedirects(response, reverse('notes:success'))
    note.refresh_from_db()
    assert note.title == form_data['title']
    assert note.text == form_data['text']
    assert note.slug == form_data['slug']


def test_other_user_cant_edit_note(
        not_author_client, form_data, note, slug_for_args
):
    url = reverse('notes:edit', args=slug_for_args)
    response = not_author_client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    # Получаем новый объект запросом из БД.
    note_from_db = Note.objects.get(pk=note.pk)
    # Проверяем что после POST-запроса данные объекта не изменились:
    assert note_from_db.title == note.title
    assert note_from_db.text == note.text
    assert note_from_db.slug == note.slug


def test_author_can_delete_note(author_client, slug_for_args):
    url = reverse('notes:delete', args=slug_for_args)
    response = author_client.post(url)
    assertRedirects(response, reverse('notes:success'))
    assert Note.objects.count() == 0


# slug_for_args создаёт объект note
def test_other_user_cant_delete_note(not_author_client, slug_for_args):
    url = reverse('notes:delete', args=slug_for_args)
    response = not_author_client.post(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Note.objects.count() == 1
