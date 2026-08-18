from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth.models import User
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Category, Product


def make_image(name='product.png'):
    buf = BytesIO()
    Image.new('RGB', (10, 10), 'red').save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type='image/png')


class BaseProductTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='viewer', password='Secret123'
        )
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Laptop Pro',
            description='Powerful laptop',
            price='1299.00',
            stock=3,
            available=True,
            image=make_image(),
        )


class ProductListTests(BaseProductTestCase):

    def test_product_list_renders_all(self):
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'product_list.html')
        self.assertEqual(len(response.context['products']), 1)

    def test_product_list_filters_by_category(self):
        other = Category.objects.create(name='Books')
        Product.objects.create(
            category=other,
            name='Novel',
            description='A book',
            price='9.99',
            stock=10,
            available=True,
            image=make_image('novel.png'),
        )
        response = self.client.get(reverse('product_list'), {'category': other.id})
        products = list(response.context['products'])
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, 'Novel')

    def test_product_list_filters_by_search(self):
        Product.objects.create(
            category=self.category,
            name='Desktop',
            description='A desktop',
            price='899.00',
            stock=2,
            available=True,
            image=make_image('desktop.png'),
        )
        response = self.client.get(reverse('product_list'), {'q': 'laptop'})
        products = list(response.context['products'])
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, 'Laptop Pro')


class ProductDetailTests(BaseProductTestCase):

    def test_product_detail_requires_login(self):
        response = self.client.get(reverse('product_detail', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_product_detail_renders_for_authenticated(self):
        self.client.login(username='viewer', password='Secret123')
        response = self.client.get(reverse('product_detail', args=[self.product.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'product_detail.html')

    def test_product_detail_missing_pk_returns_404(self):
        self.client.login(username='viewer', password='Secret123')
        response = self.client.get(reverse('product_detail', args=[9999]))
        self.assertEqual(response.status_code, 404)


class CategoryListTests(BaseProductTestCase):

    def test_category_list_renders(self):
        response = self.client.get(reverse('category_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'category_list.html')


class URLResolutionTests(TestCase):

    def test_core_urls_resolve(self):
        self.assertEqual(
            resolve(reverse('product_list')).func.__name__, 'product_list'
        )
        self.assertEqual(
            resolve(reverse('register')).func.__name__, 'register_view'
        )
        self.assertEqual(
            resolve(reverse('login')).func.__name__, 'login_view'
        )
        self.assertEqual(
            resolve(reverse('logout')).func.__name__, 'logout_view'
        )
        self.assertEqual(
            resolve(reverse('view_cart')).func.__name__, 'view_cart'
        )
        self.assertEqual(
            resolve(reverse('checkout')).func.__name__, 'checkout'
        )
        self.assertEqual(
            resolve(reverse('payment')).func.__name__, 'payment'
        )
        self.assertEqual(
            resolve(reverse('payment_success')).func.__name__, 'payment_success'
        )
        self.assertEqual(
            resolve(reverse('my_orders')).func.__name__, 'my_orders'
        )
        self.assertEqual(
            resolve(reverse('address_list')).func.__name__, 'address_list'
        )