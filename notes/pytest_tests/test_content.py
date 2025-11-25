import pytest

from django.urls import reverse
from pytest_lazy_fixtures import lf

from notes.forms import NoteForm


@pytest.mark.parametrize(
    'parametrized_client, note_in_list',
    (
        (lf('author_client'), True),
        (lf('not_author_client'), False),
    ),
)
def test_notes_list_for_different_users(
    parametrized_client, note_in_list, note
):
    url = reverse('notes:list')
    response = parametrized_client.get(url)
    # Список объектов, в котором клиент является автором
    object_list = response.context['object_list']
    # Должна ли быть заметка в списке этого пользователя.
    assert (note in object_list) is note_in_list


@pytest.mark.parametrize(
    'name, args',
    (
        ('notes:add', None),
        ('notes:edit', lf('slug_for_args')),
    ),
)
def test_pages_contain_form(author_client, name, args):
    url = reverse(name, args=args)
    response = author_client.get(url)
    # Убеждаемся, что форма есть в контексте
    assert 'form' in response.context
    assert isinstance(response.context['form'], NoteForm)
