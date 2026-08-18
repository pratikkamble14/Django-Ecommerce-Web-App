from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from product_app.models import Category, Product
from cart_app.models import Cart, CartItem
from order_app.models import Order, OrderItem


def make_image(name='product.png'):
    buf = BytesIO()
    Image.new('RGB', (10, 10), 'red').save(buf, format='PNG')
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type='image/png')


class BasePaymentTestCase(TestCase):

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
            stock=5,
            available=True,
            image=make_image(),
        )
        self.client.login(username='buyer', password='Secret123')

    def _setup_cart(self, quantity=1):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart, product=self.product, quantity=quantity
        )
        return cart

    def _checkout(self, quantity=1):
        self._setup_cart(quantity)
        return self.client.post(reverse('checkout'), {
            'address': '123 Test St',
            'city': 'Metropolis',
            'postal_code': '12345',
        })


class CheckoutTests(BasePaymentTestCase):

    def test_checkout_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_checkout_empty_cart_redirects_to_products(self):
        response = self.client.get(reverse('checkout'))
        self.assertRedirects(response, reverse('product_list'))

    def test_checkout_creates_unpaid_order_and_order_items(self):
        response = self._checkout()
        self.assertRedirects(response, reverse('payment'))
        order = Order.objects.get(user=self.user)
        self.assertFalse(order.paid)
        self.assertEqual(order.address, '123 Test St')
        items = order.items.all()
        self.assertEqual(items.count(), 1)
        self.assertEqual(items[0].product, self.product)
        self.assertEqual(items[0].quantity, 1)
        # price is snapshotted from product
        self.assertEqual(float(items[0].price), 999.99)

    def test_checkout_decrements_stock_and_clears_cart(self):
        self._checkout()
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 4)
        self.assertEqual(CartItem.objects.filter(cart__user=self.user).count(), 0)
        self.assertEqual(
            self.client.session['order_id'],
            Order.objects.get(user=self.user).id,
        )

    def test_checkout_rejects_quantity_exceeding_stock(self):
        self._setup_cart(quantity=100)
        response = self.client.post(reverse('checkout'), {
            'address': '123 Test St',
            'city': 'Metropolis',
            'postal_code': '12345',
        })
        self.assertRedirects(response, reverse('view_cart'))
        self.assertFalse(Order.objects.filter(user=self.user).exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 5)


class PaymentTests(BasePaymentTestCase):

    def test_payment_marks_order_paid_and_clears_session(self):
        self._checkout()
        order = Order.objects.get(user=self.user)
        response = self.client.post(reverse('payment'))
        self.assertRedirects(response, reverse('payment_success'))
        order.refresh_from_db()
        self.assertTrue(order.paid)
        self.assertNotIn('order_id', self.client.session)

    def test_payment_without_order_id_redirects_to_checkout(self):
        response = self.client.get(reverse('payment'))
        self.assertRedirects(
            response, reverse('checkout'), fetch_redirect_response=False
        )

    def test_payment_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('payment'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)


class PaymentSuccessTests(BasePaymentTestCase):

    def test_payment_success_confirms_paid_order(self):
        self._checkout()
        order = Order.objects.get(user=self.user)
        response = self.client.get(reverse('payment_success'))
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertTrue(order.paid)
        self.assertNotIn('order_id', self.client.session)

    def test_payment_success_without_session_is_ok(self):
        response = self.client.get(reverse('payment_success'))
        self.assertEqual(response.status_code, 200)

    def test_payment_success_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse('payment_success'))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)


class PaymentOwnershipTests(BasePaymentTestCase):

    def test_user_cannot_pay_for_another_users_order(self):
        other = User.objects.create_user(username='other', password='Secret123')
        order = Order.objects.create(
            user=other,
            address='Other St',
            city='Elsewhere',
            postal_code='99999',
        )
        # Attach session pointing at the other user's order
        session = self.client.session
        session['order_id'] = order.id
        session.save()
        response = self.client.get(reverse('payment'))
        # Should not expose the other user's order (404)
        self.assertEqual(response.status_code, 404)