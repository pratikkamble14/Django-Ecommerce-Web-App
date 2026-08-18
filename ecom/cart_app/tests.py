from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from product_app.models import Category, Product
from .models import Cart, CartItem


def make_image(name='product.png'):
    buf = BytesIO()
    Image.new('RGB', (10, 10), 'red').save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type='image/png')


class BaseCartTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='buyer', password='Secret123'
        )
        self.category = Category.objects.create(name='Electronics')
        self.product = Product.objects.create(
            category=self.category,
            name='Laptop',
            description='A laptop',
            price='999.99',
            stock=10,
            available=True,
            image=make_image(),
        )
        self.product2 = Product.objects.create(
            category=self.category,
            name='Mouse',
            description='A mouse',
            price='19.99',
            stock=5,
            available=True,
            image=make_image('mouse.png'),
        )

    def _login(self):
        self.client.login(username='buyer', password='Secret123')


class CartHelpersTests(BaseCartTestCase):

    def test_get_or_create_cart_authenticated(self):
        self._login()
        # Directly exercise the view by adding to cart
        self.client.get(reverse('add_to_cart', args=[self.product.id]))
        cart = Cart.objects.get(user=self.user)
        self.assertIsNotNone(cart)
        self.assertEqual(cart.session_key, None)

    def test_get_or_create_cart_guest_uses_session(self):
        self.client.get(reverse('add_to_cart', args=[self.product.id]))
        session_key = self.client.session.session_key
        cart = Cart.objects.get(session_key=session_key)
        self.assertIsNotNone(cart)
        self.assertIsNone(cart.user)


class AddToCartTests(BaseCartTestCase):

    def test_add_new_item(self):
        self._login()
        self.client.get(reverse('add_to_cart', args=[self.product.id]))
        cart = Cart.objects.get(user=self.user)
        item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(item.quantity, 1)

    def test_add_existing_item_increments_quantity(self):
        self._login()
        self.client.get(reverse('add_to_cart', args=[self.product.id]))
        self.client.get(reverse('add_to_cart', args=[self.product.id]))
        cart = Cart.objects.get(user=self.user)
        item = CartItem.objects.get(cart=cart, product=self.product)
        self.assertEqual(item.quantity, 2)


class ViewCartTests(BaseCartTestCase):

    def test_view_cart_computes_totals(self):
        self._login()
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        CartItem.objects.create(cart=cart, product=self.product2, quantity=3)
        response = self.client.get(reverse('view_cart'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'view_cart.html')
        cart_items = response.context['cart_items']
        self.assertEqual(len(cart_items), 2)
        # 2 * 999.99 = 1999.98 ; 3 * 19.99 = 59.97 ; total = 2059.95
        self.assertEqual(float(response.context['total_price']), 2059.95)


class UpdateCartTests(BaseCartTestCase):

    def test_update_cart_decrements_stock(self):
        self._login()
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        response = self.client.post(reverse('update_cart'), {
            f'quantity_{item.id}': '3',
        })
        self.assertRedirects(response, reverse('view_cart'))
        item.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(item.quantity, 3)
        self.assertEqual(self.product.stock, 8)

    def test_update_cart_rejects_quantity_exceeding_stock(self):
        self._login()
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        response = self.client.post(reverse('update_cart'), {
            f'quantity_{item.id}': '100',
        })
        self.assertRedirects(response, reverse('view_cart'))
        item.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(item.quantity, 1)
        self.assertEqual(self.product.stock, 10)


class RemoveFromCartTests(BaseCartTestCase):

    def test_remove_from_cart_deletes_item(self):
        self._login()
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        response = self.client.get(reverse('remove_from_cart', args=[item.id]))
        self.assertRedirects(response, reverse('view_cart'))
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())