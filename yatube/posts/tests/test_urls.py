from http import HTTPStatus
from django.test import TestCase, Client
from posts.models import Post, Group, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """Создаем юзера, группу, пост"""
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.post.author)
        self.public_pages = ['/',
                             f'/group/{self.post.group.slug}/',
                             f'/profile/{self.post.author}/',
                             f'/posts/{self.post.id}/']
        self.private_page = [f'/posts/{self.post.id}/edit/',
                             '/create/']
        self.all_page = self.private_page + self.public_pages

    def test_url_available_to_any_user(self):
        """Общедоступные страницы"""
        for page1 in self.public_pages:
            with self.subTest(public_pages=page1):
                response = self.guest_client.get(page1)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_post_edit(self):
        """Cтраница '/posts/<post_id>/edit/' доступна автору."""
        for page2 in self.all_page:
            with self.subTest(all_page=page2):
                response = self.authorized_client.get(page2)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_Client_post_edit(self):
        """Cтраница '/posts/<post_id>/edit/' не доступна не автору."""
        post_id = self.post.id
        response = self.guest_client.get(f'/posts/{post_id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_guest_post_edit(self):
        """Cтраница '/create/' не доступна гостю."""
        response = self.guest_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting(self):
        """Несуществующая страница выдаёт код 404"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        group_slug = self.post.group.slug
        post_author = self.post.author
        post_id = self.post.id
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{group_slug}/': 'posts/group_list.html',
            f'/profile/{post_author}/': 'posts/profile.html',
            f'/posts/{post_id}/': 'posts/post_detail.html',
            f'/posts/{post_id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
