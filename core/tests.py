from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from core.models import UserProfile
from core.models import (
    Item, Order, OrderItem, Address, Payment, 
    UserProfile, Promotion
)
from django.utils import timezone
from decimal import Decimal
import datetime

class PromotionsViewTestCase(TestCase):
    def setUp(self):
        # Create test items
        self.apple = Item.objects.create(
            name='Apple',
            price=Decimal('5.00'),
            stock=10,
            slug='apple',
            category='fruits'
        )
        
        # Create promotions
        self.active_promo1 = Promotion.objects.create(
            title='Fruits Sale',
            description='20% off all fruits',
            start_date=timezone.now() - datetime.timedelta(days=1),
            end_date=timezone.now() + datetime.timedelta(days=7),
            discount_rate=Decimal('20.00'),
            is_active=True
        )
        self.active_promo1.products.add(self.apple)

    # Test that promotions page returns 200 status code
    def test_promotions_view_status_code(self):
        response = self.client.get(reverse('core:promotions'))
        self.assertEqual(response.status_code, 200)

    # Test that correct template is used
    def test_promotions_view_template_used(self):
        response = self.client.get(reverse('core:promotions'))
        self.assertTemplateUsed(response, 'promotions.html')

    # Test that only active promotions within date range are displayed
    def test_only_active_promotions_shown(self):
        response = self.client.get(reverse('core:promotions'))
        
        # Check active promotions are shown
        self.assertContains(response, 'Fruits Sale')

    # Test that promotion details are correctly displayed
    def test_promotion_details_displayed(self):
        response = self.client.get(reverse('core:promotions'))
        
        # Check title, description, discount rate
        self.assertContains(response, 'Fruits Sale')
        self.assertContains(response, '20% off all fruits')

        # Check date formatting
        self.assertContains(response, self.active_promo1.end_date.strftime('%B %d, %Y'))

    # Test that products associated with promotions are shown
    def test_associated_products_displayed(self):
        response = self.client.get(reverse('core:promotions'))
        
        # Check products are linked
        self.assertContains(response, 'View Apple')
        
        # Check links are correct
        self.assertContains(response, f'href="{reverse("core:product", kwargs={"slug": "apple"})}"')

    # Test that 'no promotions' message appears when there are none
    def test_no_promotions_message(self):
        # Delete all promotions
        Promotion.objects.all().delete()
        
        response = self.client.get(reverse('core:promotions'))
        self.assertContains(response, 'No promotions available at this time.')
        self.assertNotContains(response, 'View Apple')  # No products should be shown


class CheckoutCartItemsTestCase(TestCase):
    def setUp(self):
        # Create test user
        self.username = "testuser"
        self.password = "testpass123"
        self.user = User.objects.create_user(username=self.username, password=self.password)
        
        # Create test items
        self.item1 = Item.objects.create(
            name='Apple',
            price=Decimal('5.00'),
            stock=10,
            slug='apple',
            category='fruits'
        )
        self.item2 = Item.objects.create(
            name='Carrot',
            price=Decimal('3.50'),
            stock=20,
            slug='carrot',
            category='vegetables'
        )
        
        # Create promotion only for apples
        self.fruit_promotion = Promotion.objects.create(
            title='Fruits Sale',
            description='20% off all fruits',
            start_date=timezone.now() - datetime.timedelta(days=1),
            end_date=timezone.now() + datetime.timedelta(days=7),
            discount_rate=Decimal('20.00'),
            is_active=True
        )
        self.fruit_promotion.products.add(self.item1)
        
        # Create a cart with items
        self.order = Order.objects.create(
            user=self.user,
            is_ordered=False
        )
        self.order_item1 = OrderItem.objects.create(
            item=self.item1,
            user=self.user,
            quantity=3,  # 3 apples
            ordered=False,
            order_id=self.order.id
        )
        self.order_item2 = OrderItem.objects.create(
            item=self.item2,
            user=self.user,
            quantity=2,  # 2 carrots
            ordered=False,
            order_id=self.order.id
        )
        self.order.items.add(self.order_item1, self.order_item2)

    # Test that all cart items are displayed correctly
    def test_cart_items_display(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('core:checkout-page'))
        
        self.assertEqual(response.status_code, 200)
        
        # Check all items are displayed
        self.assertContains(response, 'Apple')
        self.assertContains(response, 'Carrot')
        
        # Check quantities
        self.assertContains(response, '3 x Apple')
        self.assertContains(response, '2 x Carrot')
        
        # Check categories
        self.assertContains(response, 'Fruits')
        self.assertContains(response, 'Vegetables')

    # Test individual item final prices are correct
    def test_item_final_price_calculation(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('core:checkout-page'))
        
        # Apple: 3 x $5 = $15 - 20% = $12.00
        self.assertContains(response, '$12.00')
        
        # Carrot: 2 x $3.50 = $7.00 (no discount)
        self.assertContains(response, '$7.00')

    # Test discount amounts are calculated correctly
    def test_discount_calculation(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('core:checkout-page'))
        
        # Discounts:
        # Apples: 20% off $15 = $3
        # Carrots: no discount
        # Total discount: $3.00
        self.assertContains(response, '$3.00')

    # Test subtotal after discounts is correct
    def test_discounted_subtotal(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('core:checkout-page'))
        
        # Subtotal after discounts:
        # $22 (original) - $3 (discounts) = $19
        self.assertContains(response, '$19.00')

    # Test tax is calculated correctly on discounted subtotal
    def test_tax_calculation(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('core:checkout-page'))
        
        # Tax (13% of $19) = $2.47
        self.assertContains(response, '$2.47')

    # Test final price includes discounts and tax
    def test_final_price_calculation(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('core:checkout-page'))
        
        # Final price:
        # $19 (discounted subtotal) + $2.47 (tax) = $21.47
        self.assertContains(response, '$21.47')

class LoginTestCase(TestCase):

    def setUp(self):
        self.username = "testuser"
        self.password = "testpass123"
        self.user = User.objects.create_user(username=self.username, password=self.password)

    # Login with correct credentials
    def test_login_success(self):
        response = self.client.post(reverse('account_login'), {
            'login': self.username,       #  'login' covers username 
            'password': self.password
        })
        self.assertEqual(response.status_code, 302)  # successful login usually redirects
        self.assertRedirects(response, '/')  

    def test_login_failure_wrong_password(self):
        response = self.client.post(reverse('account_login'), {
            'login': self.username,
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The username and/or password you specified are not correct.")

    def test_login_failure_nonexistent_user(self):
        response = self.client.post(reverse('account_login'), {
            'login': 'notarealuser',
            'password': 'whatever'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The username and/or password you specified are not correct.")

    def test_login_redirects_to_next(self):
        login_url = reverse('account_login') + '?next=/'
        response = self.client.post(login_url, {
            'login': self.username,
            'password': self.password
        })
        self.assertRedirects(response, '/')



class MultiStepSignupTestCase(TestCase):

    # Full multi-step signup flow (signup + complete profile)
    def test_full_signup_flow_success(self):
        # Step 1: Sign up using Allauth
        response = self.client.post(reverse('account_signup'), {
            'username': 'signupuser',
            'email': 'signupuser@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 302)  # should redirect (probably to complete-profile)

        #  User should exist
        self.assertTrue(User.objects.filter(username='signupuser').exists())

        #  Log in the newly created user
        self.client.login(username='signupuser', password='TestPass123!')

        # Step 2: Complete profile
        response = self.client.post(reverse('core:complete_profile'), {
            'first_name': 'Test',
            'last_name': 'User',
            'address': '123 Main St',
            'city': 'Toronto',
            'postal_code': 'M1A1A1',
            'phone': '1234567890'
        })

        self.assertEqual(response.status_code, 302)  # should redirect to account or home

        user = User.objects.get(username='signupuser')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')

        profile = user.userprofile
        self.assertEqual(profile.address, '123 Main St')
        self.assertEqual(profile.city, 'Toronto')
        self.assertEqual(profile.postal_code, 'M1A1A1')
        self.assertEqual(profile.phone, '1234567890')

    # Complete profile should reject missing required fields
    def test_profile_required_fields_enforced(self):
        # Step 1: Sign up user
        self.client.post(reverse('account_signup'), {
            'username': 'incompleteuser',
            'email': 'incomplete@example.com',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        self.client.login(username='incompleteuser', password='TestPass123!')

        # Step 2: Submit profile with missing required fields
        response = self.client.post(reverse('core:complete_profile'), {
            'first_name': '',  # missing
            'last_name': 'Doe',
            'address': '',     # missing
            'city': '',        # missing
            'postal_code': '', # missing
            'phone': ''        # optional
        })

        # Should not redirect, form should error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required', count=4)  # 4 required fields missing

    # Signup fails with mismatched passwords
    def test_signup_password_mismatch(self):
        response = self.client.post(reverse('account_signup'), {
            'username': 'badpassuser',
            'email': 'badpass@example.com',
            'password1': 'TestPass123!',
            'password2': 'Mismatch123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You must type the same password each time.')
        self.assertFalse(User.objects.filter(username='badpassuser').exists())

    # Signup fails with an already existing username
    def test_signup_existing_username(self):
        User.objects.create_user(username='duplicateuser', password='SomePass123!')

        response = self.client.post(reverse('account_signup'), {
            'username': 'duplicateuser',
            'email': 'duplicate@example.com',
            'password1': 'AnotherPass123!',
            'password2': 'AnotherPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'A user with that username already exists.')

    # invalid email
    def test_signup_invalid_email(self):
        response = self.client.post(reverse('account_signup'), {
            'username': 'invalidemail',
            'email': 'not-an-email',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter a valid email address.')

    # Cannot access complete-profile page without login
    def test_complete_profile_requires_login(self):
        response = self.client.get(reverse('core:complete_profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login', response.url)


class AccountViewTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='accuser', email='acc@example.com', password='Testpass123!')
        self.user.first_name = 'John'
        self.user.last_name = 'Doe'
        self.user.save()

        self.profile = UserProfile.objects.create(
            user=self.user,
            address='123 Road St',
            city='Toronto',
            postal_code='M3C1A1',
            phone='1234567890'
        )
    # Only logged-in users can view the account page
    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('core:account'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login', response.url)

    # Account data renders properly
    def test_view_account_page_authenticated(self):
        self.client.login(username='accuser', password='Testpass123!')
        response = self.client.get(reverse('core:account'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John')
        self.assertContains(response, 'Doe')
        self.assertContains(response, 'acc@example.com')
        self.assertContains(response, 'Toronto')

    # form updates both User and UserProfile
    def test_account_update_post(self):
        self.client.login(username='accuser', password='Testpass123!')
        response = self.client.post(reverse('core:account'), {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'new@example.com',
            'address': '456 New St',
            'city': 'Montreal',
            'postal_code': 'H2X1Y4',
            'phone': '9998887777'
        })

        self.assertRedirects(response, reverse('core:account'))
        updated_user = User.objects.get(pk=self.user.pk)
        updated_profile = updated_user.userprofile
        self.assertEqual(updated_user.first_name, 'Jane')
        self.assertEqual(updated_user.email, 'new@example.com')
        self.assertEqual(updated_profile.city, 'Montreal')
        self.assertEqual(updated_profile.phone, '9998887777')


    # Edit mode form renders with pre-filled data
    def test_edit_mode_form_renders(self):
        self.client.login(username='accuser', password='Testpass123!')
        response = self.client.get(reverse('core:account') + '?edit=true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="John"')
        self.assertContains(response, 'value="Toronto"')

    # checking required fields
    def test_update_missing_required_fields(self):
        self.client.login(username='accuser', password='Testpass123!')
        response = self.client.post(reverse('core:account'), {
            'first_name': '',
            'last_name': '',
            'email': '',
            'address': '',
            'city': '',
            'postal_code': '',
            'phone': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required', count=5)

    # Invalid email
    def test_update_invalid_email(self):
        self.client.login(username='accuser', password='Testpass123!')
        response = self.client.post(reverse('core:account'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'invalid-email',
            'address': '456 New St',
            'city': 'Ottawa',
            'postal_code': 'K1A0B1',
            'phone': '1234567890'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter a valid email address.')

    # Check correct template is used
    def test_template_used(self):
        self.client.login(username='accuser', password='Testpass123!')
        response = self.client.get(reverse('core:account'))
        self.assertTemplateUsed(response, 'account.html')


class AccountEditTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='edituser',
            email='old@example.com',
            password='SecurePass123'
        )
        self.user.first_name = 'OldFirst'
        self.user.last_name = 'OldLast'
        self.user.save()

        UserProfile.objects.create(
            user=self.user,
            address='Old Address',
            city='Old City',
            postal_code='A1A1A1',
            phone='0000000000'
        )

    #  Successful update of User and Profile fields
    def test_account_edit_successful(self):
        self.client.login(username='edituser', password='SecurePass123')

        response = self.client.post(reverse('core:account'), {
            'first_name': 'NewFirst',
            'last_name': 'NewLast',
            'email': 'new@example.com',
            'address': 'New Address',
            'city': 'New City',
            'postal_code': 'B2B2B2',
            'phone': '1234567890',
        })

        # Should redirect back to the account page
        self.assertRedirects(response, reverse('core:account'))

        # Check database values updated
        updated_user = User.objects.get(username='edituser')
        profile = updated_user.userprofile

        self.assertEqual(updated_user.first_name, 'NewFirst')
        self.assertEqual(updated_user.last_name, 'NewLast')
        self.assertEqual(updated_user.email, 'new@example.com')
        self.assertEqual(profile.address, 'New Address')
        self.assertEqual(profile.city, 'New City')
        self.assertEqual(profile.postal_code, 'B2B2B2')
        self.assertEqual(profile.phone, '1234567890')

    # Must be logged in to access account
    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse('core:account'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    # Edit page shows current user info
    def test_account_edit_form_loads_with_data(self):
        self.client.login(username='edituser', password='SecurePass123')
        response = self.client.get(reverse('core:account') + '?edit=true')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'OldFirst')
        self.assertContains(response, 'OldLast')
        self.assertTemplateUsed(response, 'account.html')


    # Form validation catches missing required field
    def test_account_edit_missing_required_fields(self):
        self.client.login(username='edituser', password='SecurePass123')
        response = self.client.post(reverse('core:account'), {
            'first_name': '',
            'last_name': '',
            'email': '',
            'address': '',
            'city': '',
            'postal_code': '',
            'phone': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'This field is required', count=5)

    # Invalid email address blocked
    def test_account_edit_invalid_email(self):
        self.client.login(username='edituser', password='SecurePass123')
        response = self.client.post(reverse('core:account'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'invalid-email',
            'address': '123 Street',
            'city': 'TestCity',
            'postal_code': 'Z1Z1Z1',
            'phone': '1234567890'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Enter a valid email address.')