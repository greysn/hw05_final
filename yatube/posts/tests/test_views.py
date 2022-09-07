from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, User
from posts.forms import PostForm
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

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            group=cls.group
        )
        cls.group1 = Group.objects.create(
            title='Тестовая группа1',
            slug='test_slug1',
            description='Тестовое описание1'
        )
        cls.post1 = Post.objects.create(
            text='Тестовый текст',
            group=cls.group1,
            author=cls.user
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
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsViewsTest.post.author)
        self.post_author = Client()
        self.post_author.force_login(self.author)

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

    def _assert_post_has_attribs(self, post, id, author, group):
        self.assertEqual(post.id, id)
        self.assertEqual(post.author, author)
        self.assertEqual(post.group, group)

    def test_index_page_context(self):
        """Шаблон index с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author = first_object.author.username
        post_text = first_object.text
        post_group = first_object.group.title
        self.assertEqual(post_author, 'testuser')
        self.assertEqual(post_text, 'Тестовый текст')
        self.assertEqual(post_group, 'Тестовая группа1')

    def test_group_list_context(self):
        """Шаблон group_list с правильным контекстом"""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test_slug'})
        )
        post = response.context['page_obj'][0]
        self.assertEqual(post.author.username, self.post.author.username)
        self.assertEqual(post.text, 'Тестовый текст')

    def test_profile_context(self):
        """Шаблон profile с правильным контекстом"""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': f'{self.user}'})
        )
        post = response.context['page_obj'][0]
        self.assertEqual(post.author.username, 'testuser')
        self.assertEqual(post.text, 'Тестовый текст')
        self.assertEqual(
            post.group.title, 'Тестовая группа1'
        )

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
        for i in range(0, ALL_PAGES):
            cls.post = Post.objects.create(
                author=cls.user,
                group=cls.group,
                text='Тестовый текст',
            )
        cls.paginate_dict = {
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
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_first_page_views(self):
        """views - На первой странице должно быть 10 постов"""
        for address, temp in self.paginate_dict.items():
            with self.subTest(temp=temp):
                danger_message = f'На странице {temp} не 10 постов'
                response = (self.authorized_client.get(address))
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
