from django.test import TestCase
from django.urls import reverse

from .forms import UserRegistrationForm
from .models import District, Role, State, User, UserTransfer


class UserFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.state = State.objects.create(name='Test State')
        cls.other_state = State.objects.create(name='Other State')
        cls.district = District.objects.create(state=cls.state, name='District One')
        cls.other_district = District.objects.create(state=cls.other_state, name='District Two')
        cls.state_role = Role.objects.create(name='STATE_ADMIN')
        cls.district_role = Role.objects.create(name='DISTRICT_ADMIN')
        cls.common_role = Role.objects.create(name='COMMON_USER')

        cls.state_admin = User.objects.create_user(
            username='state_admin', password='StrongPass123!', mobile='1000000001',
            role=cls.state_role, state=cls.state,
        )
        cls.district_admin = User.objects.create_user(
            username='district_admin', password='StrongPass123!', mobile='1000000002',
            role=cls.district_role, state=cls.state, district=cls.district,
        )
        cls.common_user = User.objects.create_user(
            username='common_user', password='StrongPass123!', mobile='1000000003',
            role=cls.common_role, state=cls.state, district=cls.district,
        )
        cls.outside_user = User.objects.create_user(
            username='outside_user', password='StrongPass123!', mobile='1000000004',
            role=cls.common_role, state=cls.other_state, district=cls.other_district,
        )

    def test_public_login_and_protected_dashboard(self):
        self.assertEqual(self.client.get(reverse('login')).status_code, 200)
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, reverse('login'), fetch_redirect_response=False)

    def test_login_dashboard_logout_flow(self):
        response = self.client.post(reverse('login'), {
            'username': self.common_user.username,
            'password': 'StrongPass123!',
        })
        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse('dashboard')).status_code, 200)
        self.assertRedirects(
            self.client.post(reverse('logout')),
            reverse('login'),
            fetch_redirect_response=False,
        )

    def test_user_lists_are_limited_by_role(self):
        self.client.force_login(self.district_admin)
        response = self.client.get(reverse('user_list'))
        self.assertSetEqual(
            {user.username for user in response.context['users']},
            {'district_admin', 'common_user'},
        )

        self.client.force_login(self.common_user)
        response = self.client.get(reverse('user_list'))
        self.assertEqual(list(response.context['users']), [self.common_user])

    def test_district_admin_cannot_edit_user_in_another_district(self):
        self.client.force_login(self.district_admin)
        response = self.client.get(reverse('edit_profile', args=[self.outside_user.pk]))
        self.assertRedirects(response, reverse('dashboard'), fetch_redirect_response=False)

    def test_state_admin_can_transfer_user(self):
        self.client.force_login(self.state_admin)
        response = self.client.post(reverse('transfer_user'), {
            'user_id': self.common_user.pk,
            'district': self.other_district.pk,
        })
        self.assertRedirects(response, reverse('user_list'), fetch_redirect_response=False)
        self.common_user.refresh_from_db()
        self.assertEqual(self.common_user.district, self.other_district)
        self.assertEqual(self.common_user.state, self.other_state)
        self.assertTrue(UserTransfer.objects.filter(user=self.common_user).exists())

    def test_state_admin_cannot_deactivate_self(self):
        self.client.force_login(self.state_admin)
        self.client.post(reverse('toggle_active', args=[self.state_admin.pk]))
        self.state_admin.refresh_from_db()
        self.assertTrue(self.state_admin.is_active)

    def test_registration_rejects_district_from_another_state(self):
        form = UserRegistrationForm(data={
            'username': 'new_user',
            'email': 'new@example.com',
            'mobile': '1000000005',
            'role': self.common_role.pk,
            'state': self.state.pk,
            'district': self.other_district.pk,
            'password': 'StrongPass123!',
            'password_confirm': 'StrongPass123!',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('district', form.errors)

    def test_registration_rejects_weak_password(self):
        form = UserRegistrationForm(data={
            'username': 'weak_user',
            'email': 'weak@example.com',
            'mobile': '1000000006',
            'role': self.common_role.pk,
            'state': self.state.pk,
            'district': self.district.pk,
            'password': 'password',
            'password_confirm': 'password',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_jwt_login_and_api_root(self):
        root = self.client.get(reverse('api_root'))
        self.assertEqual(root.status_code, 200)
        response = self.client.post(
            reverse('api_login'),
            {'username': self.common_user.username, 'password': 'StrongPass123!'},
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.json())
        self.assertIn('refresh', response.json())
