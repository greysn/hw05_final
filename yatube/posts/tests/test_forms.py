from http import HTTPStatus
from django.test import Client, TestCase
from django.urls import reverse
from posts.models import Group, Post, User


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post = Post.objects.create(
            text='Тестовый пост',
            author=self.user,
        )
        self.group = Group.objects.create(
            title='Название',
            description='Описание',
            slug='test-slug'
        )
        self.group_other = Group.objects.create(
            title='Название другой группы',
            description='Описание другой группы',
            slug='test-other-slug'
        )
        self.EDIT_POST = reverse('posts:post_edit',
                                 args=[10])

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_create_post(self):
        count_posts = Post.objects.count()
        form_data = {
            'text': 'form_text',
            'group': self.group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.post.author},
        )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post = Post.objects.exclude(id=self.post.id).first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, self.group)

    def test_create_post_guest(self):
        form_data = {
            'text': 'form_text',
            'group': self.group.id
        }
        response_guest = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=False
        )
        self.assertEqual(response_guest.status_code, HTTPStatus.FOUND)

    def test_edit_post(self):
        after_text = self.post
        self.group2 = Group.objects.create(
            title='test_title_2',
            slug='test_slug',
            description='Тестовое описание'
        )
        form_data = {
            'text': 'form_text',
            'group': self.group2.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': after_text.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.first().text, 'form_text')
        self.assertEqual(Post.objects.first().group, self.group2)
