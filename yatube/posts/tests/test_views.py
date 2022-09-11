import os
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post, User, Follow
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.forms import PostForm
from http import HTTPStatus
from posts.settings import ALL_PAGES, LIST_LENGHT, SECOND_PAGE_POST


@override_settings()
class PostsViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testuser')
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded_file = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            group=cls.group,
            image=cls.uploaded_file)

        cls.follower = Follow.objects.create(
            user=cls.user,
            author=cls.author
        )

        cls.context_test = {
            reverse('posts:index'): 'Главная страница',
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ): 'Страница групп',
            reverse(
                'posts:profile',
                kwargs={'username': cls.post.author}
            ): 'Страница профиля',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post.id}
            ): 'Страница деталей поста',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.id}
            ): 'Страница создания поста'
        }
        cls.post_with_views = {
            reverse('posts:index'): 'Главная страница',
            reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ): 'Страница групп',
            reverse(
                'posts:profile',
                kwargs={'username': cls.post.author}
            ): 'Страница профиля',
        }
        cls.templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': cls.group.slug}
            ),
            'posts/profile.html': reverse(
                'posts:profile',
                kwargs={'username': cls.post.author}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail',
                kwargs={'post_id': cls.post.id}
            ),
            'posts/create_post.html': reverse(
                'posts:post_edit',
                kwargs={'post_id': cls.post.id}
            )
        }
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        image_path = cls.post.image.path
        if image_path and os.path.isfile(image_path):
            os.remove(image_path)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsViewsTest.post.author)
        self.post_author = Client()
        self.post_author.force_login(self.author)
        self.user_client = Client()
        self.user_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for template, reverse_name in self.templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_uses_correct_template_for_guest(self):
        """URL-адрес не использует шаблон для
         не авторизованного пользователя"""
        response = self.guest_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertTemplateNotUsed(response, 'posts/create_post.html')

    def _assert_post_has_attribs(self, post):
        self.assertEqual(post.author, self.author,
                         'Автор поста не соответствует.')
        self.assertEqual(post.text, self.post.text,
                         'Содержимое поста не соответствует.')
        self.assertEqual(post.group, self.group,
                         'Группа не соответствует')

    def test_index_page_context(self):
        """Шаблон index с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self._assert_post_has_attribs(first_object)

    def test_group_list_context(self):
        """Шаблон group_list с правильным контекстом"""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug})
        )
        context_group = response.context['group']
        self.assertTrue(self.group.slug == context_group.slug,
                        'slug группы не совпадает: '
                        f'{self.group.slug} - {context_group.slug}')
        post = response.context['page_obj'][0]
        self._assert_post_has_attribs(post)

    def test_profile_context(self):
        """Шаблон profile с правильным контекстом"""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.author.username})
        )
        post = response.context['page_obj'][0]
        self._assert_post_has_attribs(post)

    def test_create_post_edit_context(self):
        """Шаблон post_edit с правильным контекстом"""
        response = self.post_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': f'{self.post.id}'})
        )
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], PostForm)
        self.assertIn('is_edit', response.context)
        self.assertEqual(response.context['is_edit'], True)
        self.assertIn('post', response.context)
        self.assertEqual(response.context['post'], self.post)

    def test_create_post_context(self):
        """Шаблон create_post с правильным контекстом"""
        response = self.authorized_client.get(reverse(
            'posts:post_create'))
        self.assertIsInstance(response.context['form'], PostForm)

    def test_post_with_group_index_show_correct_context(self):
        """Пост с группой есть на главной странице."""
        for address, temp in self.post_with_views.items():
            with self.subTest(temp=temp):
                danger_message = f'Пост {temp} не найден на странице'
                response = (self.authorized_client.get(address))
                post = response.context['page_obj'][-1]
                self.assertEqual(post.pk, self.post.pk, danger_message)

    def test_post_with_image_correct_context(self):
        """При выводе поста с картинкой изображение
        передается в словаре context"""
        url = reverse('posts:index')
        response = self.authorized_client.get(url)
        post = response.context.get('page_obj')[0]
        image_name = post.image.name.split('/')[-1]
        self.assertEqual(image_name, self.uploaded_file.name,
                         'Полученное изображение требует соответствия.')
        self._assert_post_has_attribs(post)

    def test_follow_index_context(self):
        """ Проверка ленты подписок """
        response = self.user_client.get(reverse('posts:follow_index'))
        first_object = response.context['page_obj'][0]
        self._assert_post_has_attribs(first_object)
        Follow.objects.create(user=self.user, author=self.author)

    def test_author_follow(self):
        """ Проверка возможности подписаться на автора """
        Follow.objects.filter(user=self.user, author=self.author).delete()
        old_follow_count = Follow.objects.filter(user=self.user).count()
        _url = reverse('posts:profile_follow', args=(self.author.username,))
        response = self.user_client.get(_url)
        self.assertEqual(
            response.status_code, HTTPStatus.FOUND,
            f'Ошибка подписки: {_url} - {self.user}, {self.author}')
        new_follow_count = Follow.objects.filter(user=self.user).count()
        self.assertEqual(new_follow_count, old_follow_count + 1,
                         'Количество подписок не увеличилось: '
                         f'{old_follow_count} <-> {new_follow_count}')

    def test_author_unfollow(self):
        """ Проверка возможности отписаться от автора """
        old_follow_count = Follow.objects.filter(user=self.user).count()
        _url = reverse('posts:profile_unfollow', args=(self.author.username,))
        response = self.user_client.get(_url)
        self.assertEqual(
            response.status_code, HTTPStatus.FOUND,
            f'Ошибка отписки: {_url} - {self.user}, {self.author}')
        new_follow_count = Follow.objects.filter(user=self.user).count()
        self.assertEqual(new_follow_count, old_follow_count - 1,
                         'Количество подписок не уменьшилось: '
                         f'{old_follow_count} <-> {new_follow_count}')


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        for i in range(ALL_PAGES):
            cls.post = Post.objects.create(
                author=cls.user,
                group=cls.group,
                text='Тестовый текст',
            )
        cls.paginate_dict = {
            reverse('posts:index'): 'Главная страница',
            reverse('posts:group_list',
                    kwargs={'slug': cls.group.slug}): 'Страница групп',
            reverse('posts:profile',
                    kwargs={'username': cls.post.author}): 'Страница профиля'
        }
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_first_page_views(self):
        """views - На первой странице должно быть 10 постов"""
        for address, temp in self.paginate_dict.items():
            with self.subTest(temp=temp):
                danger_message = f'На странице {temp} не 10 постов'
                response = self.authorized_client.get(address)
                self.assertEqual(len(response.context['page_obj']),
                                 LIST_LENGHT, danger_message)

    def test_second_page_views(self):
        """Views - На второй странице должно быть 3 поста"""
        for address, temp in self.paginate_dict.items():
            with self.subTest(temp=temp):
                danger_message = f'На странице {temp} не 3 постa'
                response = (self.authorized_client.get(address + '?page=2'))
                self.assertEqual(len(response.context['page_obj']),
                                 SECOND_PAGE_POST, danger_message)

    def test_comment_to_post_detail(self):
        """Комментарий появляется на странице поста."""
        comments_count = Comment.objects.count()
        comment_new = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Тестовый комментарий')
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(
            Comment.objects.first().text,
            comment_new.text)
