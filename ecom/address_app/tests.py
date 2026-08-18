from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Address


class BaseAddressTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='alice', password='Secret123'
        )
        self.other = User.objects.create_user(
            username='bob', password='Secret123'
        )
        self.address = Address.objects.create(
            user=self.user,
            full_name='Alice',
            phone='1234567890',
            address_line1='1 Main St',
            city='Springfield',
            state='IL',
            postal_code='62701',
            country='USA',
        )

    def _login(self):
        self.client.login(username='alice', password='Secret123')


class AddressRequiresLoginTests(BaseAddressTestCase):

    def test_address_views_require_login(self):
        for url in [
            reverse('address_list'),
            reverse('address_create'),
            reverse('address_update', args=[self.address.id]),
            reverse('address_delete', args=[self.address.id]),
        ]:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('login'), response.url)


class AddressCRUDTests(BaseAddressTestCase):

    def test_create_address(self):
        self._login()
        response = self.client.post(reverse('address_create'), {
            'full_name': 'Alice Smith',
            'phone': '5551234',
            'address_line1': '9 Oak Ave',
            'address_line2': '',
            'city': 'Chicago',
            'state': 'IL',
            'postal_code': '60601',
            'country': 'USA',
            'is_default': False,
        })
        self.assertRedirects(response, reverse('address_list'))
        self.assertTrue(Address.objects.filter(user=self.user).exists())

    def test_list_returns_only_own_addresses(self):
        self._login()
        response = self.client.get(reverse('address_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['addresses'].values_list('id', flat=True)),
            list(Address.objects.filter(user=self.user).values_list('id', flat=True)),
        )

    def test_update_own_address(self):
        self._login()
        response = self.client.post(
            reverse('address_update', args=[self.address.id]),
            {
                'full_name': 'Alice Updated',
                'phone': '5551234',
                'address_line1': '9 Oak Ave',
                'address_line2': '',
                'city': 'Chicago',
                'state': 'IL',
                'postal_code': '60601',
                'country': 'USA',
                'is_default': False,
            },
        )
        self.assertRedirects(response, reverse('address_list'))
        self.address.refresh_from_db()
        self.assertEqual(self.address.full_name, 'Alice Updated')

    def test_delete_own_address(self):
        self._login()
        response = self.client.post(
            reverse('address_delete', args=[self.address.id])
        )
        self.assertRedirects(response, reverse('address_list'))
        self.assertFalse(Address.objects.filter(id=self.address.id).exists())

    def test_delete_requires_post(self):
        self._login()
        response = self.client.get(
            reverse('address_delete', args=[self.address.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Address.objects.filter(id=self.address.id).exists())


class AddressOwnershipTests(BaseAddressTestCase):

    def test_cannot_update_others_address(self):
        self._login()
        other_address = Address.objects.create(
            user=self.other,
            full_name='Bob',
            phone='0',
            address_line1='2 Other St',
            city='Nowhere',
            state='CA',
            postal_code='90001',
            country='USA',
        )
        response = self.client.post(
            reverse('address_update', args=[other_address.id]),
            {
                'full_name': 'Hijacked',
                'phone': '0',
                'address_line1': '2 Other St',
                'address_line2': '',
                'city': 'Nowhere',
                'state': 'CA',
                'postal_code': '90001',
                'country': 'USA',
                'is_default': False,
            },
        )
        self.assertEqual(response.status_code, 404)

    def test_cannot_delete_others_address(self):
        self._login()
        other_address = Address.objects.create(
            user=self.other,
            full_name='Bob',
            phone='0',
            address_line1='2 Other St',
            city='Nowhere',
            state='CA',
            postal_code='90001',
            country='USA',
        )
        response = self.client.post(
            reverse('address_delete', args=[other_address.id])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Address.objects.filter(id=other_address.id).exists())