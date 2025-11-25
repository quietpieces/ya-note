"""Тесты, проверяющие доступность страниц."""
from http import HTTPStatus
import pytest

from django.urls import reverse
from pytest_lazy_fixtures import lf
from pytest_django.asserts import assertRedirects


@pytest.mark.parametrize(
        'name',
        ('notes:home', 'users:login', 'users:signup')
)
def test_pages_availability_for_anonymous_client(client, name):
    """Проверка доступности домашней страницы, страниц логина и регистрации."""
    url = reverse(name)
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK


def test_anonymous_client_get_logout(client):
    """Проверяет, что страница логаута не принимает GET-запрос."""
    url = reverse('users:logout')
    response = client.get(url)
    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


@pytest.mark.parametrize(
        'name',
        ('notes:list', 'notes:add', 'notes:success')
)
def test_pages_availability_for_auth_user(not_author_client, name):
    """Доступность страницы с заметками, создания и успешного создания."""
    url = reverse(name)
    response = not_author_client.get(url)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    'parametrized_client, expected_status',
    [
        (lf('not_author_client'), HTTPStatus.NOT_FOUND),
        (lf('author_client'), HTTPStatus.OK)
    ],
)
@pytest.mark.parametrize(
    'name, args',
    (
        ('notes:detail', lf('slug_for_args')),
        ('notes:edit', lf('slug_for_args')),
        ('notes:delete', lf('slug_for_args')),
    ),
)
def test_pages_availability_for_different_users(
    parametrized_client, name, args, expected_status
):
    """
    Доступность страниц взаимодействия с заметками.

    Проверка доступности для автора и другого пользователя.
    """
    # slug_for_args -> tuple[note.slug]
    url = reverse(name, args=args)
    response = parametrized_client.get(url)
    assert response.status_code == expected_status


@pytest.mark.parametrize(
        'name, args',
        (
            ('notes:delete', lf('slug_for_args')),
            ('notes:detail', lf('slug_for_args')),
            ('notes:edit', lf('slug_for_args')),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        ),
)
def test_redirects(client, name, args):
    """Проверка редиректов на страницу логина, для анонимного клиента."""
    login_url = reverse('users:login')
    url = reverse(name, args=args)
    expected_url = f'{login_url}?next={url}'
    response = client.get(url)
    assertRedirects(response, expected_url)
