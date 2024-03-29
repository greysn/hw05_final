from django.test import TestCase
from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.post = Post.objects.create(
            text='a' * 20,
            author=User.objects.create_user(username='testuser')
        )
        cls.TEXT_FIELD = 'text'
        cls.GROUP_FIELD = 'group'

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            self.TEXT_FIELD: 'Текст',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            self.GROUP_FIELD: 'Группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    Post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        field_help_texts = {
            self.TEXT_FIELD: 'Введите текст поста',
            self.GROUP_FIELD: 'Введите описание группы',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    Post._meta.get_field(value).help_text, expected)

    def test_object_name_is_title_fild(self):
        """Первые пятнадцать символов поста в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        expected_object_name = post.text[:15]
        self.assertEqual(expected_object_name, str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовое название',
            description='Тестовое описание'
        )

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        field_verboses = {
            'title': 'Название',
            'slug': 'Ссылка',
            'description': 'Описание',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    Group._meta.get_field(value).verbose_name, expected)

    def test_object_str(self):
        """Проверка для класса Group — название группы"""
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEqual(expected_object_name, str(group))
