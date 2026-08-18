from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from product_app.models import Category, Product
from cart_app.models import Cart, CartItem
from .models import Order, OrderItem


def make_image(name='product.png'):
    buf = BytesIO()
    Image.new('RGB', (10, 10), 'red').save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type='image/png')


class BaseOrderTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='buyer', password='Secret123'
        )
        self.other = User.objects.create_user(
            username='other', password='Secret123'
        )
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Laptop',
            description='A laptop',
            price='999.99',
            stock=5,
            available=True,
            image=make_image(),
        )
        self.client.login(username='buyer', password='Secret123')

    def _setup_cart(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        return cart


class CreateOrderTests(BaseOrderTestCase):

    def test_create_order_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('create_order'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_create_order_creates_order_and_items(self):
        self._setup_cart()
        response = self.client.post(reverse('create_order'), {
            'address': '123 Test St',
            'city': 'Metropolis',
            'postal_code': '12345',
        })
        order = Order.objects.get(user=self.user)
        self.assertRedirects(response, reverse('order_summary', args=[order.id]))
        self.assertEqual(order.address, '123 Test St')
        items = order.items.all()
        self.assertEqual(items.count(), 1)
        self.assertEqual(items[0].quantity, 2)
        self.assertEqual(float(items[0].price), 999.99)


class MyOrdersTests(BaseOrderTestCase):

    def test_my_orders_returns_only_own_orders(self):
        Order.objects.create(
            user=self.other,
            address='Other St',
            city='Elsewhere',
            postal_code='99999',
        )
        mine = Order.objects.create(
            user=self.user,
            address='123 Test St',
            city='Metropolis',
            postal_code='12345',
        )
        response = self.client.get(reverse('my_orders'))
        self.assertEqual(response.status_code, 200)
        orders = list(response.context['orders'])
        self.assertEqual(orders, [mine])


class OrderSummaryTests(BaseOrderTestCase):

    def test_order_summary_renders_own_order(self):
        order = Order.objects.create(
            user=self.user,
            address='123 Test St',
            city='Metropolis',
            postal_code='12345',
        )
        OrderItem.objects.create(
            order=order, product=self.product, price='999.99', quantity=2
        )
        response = self.client.get(reverse('order_summary', args=[order.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'order_summary.html')

    def test_order_summary_hides_others_order(self):
        order = Order.objects.create(
            user=self.other,
            address='Other St',
            city='Elsewhere',
            postal_code='99999',
        )
        response = self.client.get(reverse('order_summary', args=[order.id]))
        self.assertEqual(response.status_code, 404)


class DeleteOrderTests(BaseOrderTestCase):

    def test_delete_own_order(self):
        order = Order.objects.create(
            user=self.user,
            address='123 Test St',
            city='Metropolis',
            postal_code='12345',
        )
        response = self.client.post(reverse('delete_order', args=[order.id]))
        self.assertRedirects(response, reverse('my_orders'))
        self.assertFalse(Order.objects.filter(id=order.id).exists())

    def test_delete_requires_post(self):
        order = Order.objects.create(
            user=self.user,
            address='123 Test St',
            city='Metropolis',
            postal_code='12345',
        )
        response = self.client.get(reverse('delete_order', args=[order.id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Order.objects.filter(id=order.id).exists())

    def test_delete_others_order_returns_404(self):
        order = Order.objects.create(
            user=self.other,
            address='Other St',
            city='Elsewhere',
            postal_code='99999',
        )
        response = self.client.post(reverse('delete_order', args=[order.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Order.objects.filter(id=order.id).exists())