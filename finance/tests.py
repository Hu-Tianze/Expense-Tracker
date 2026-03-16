from decimal import Decimal
from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.test.utils import override_settings
from django.utils.http import urlencode
from django.core.cache import cache
from rest_framework.test import APIClient
from unittest.mock import patch

from finance.models import Category, Transaction, RiskAlert
from finance.utils import get_exchange_rate
from finance.constants import TRANSACTION_PAGE_SIZE
from user.models import User
from user.models import EmailOTP as UserEmailOTP


class FinanceViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="alice@example.com",
            password="StrongPass123!",
            name="Alice",
        )
        self.other_user = User.objects.create_user(
            email="bob@example.com",
            password="StrongPass123!",
            name="Bob",
        )
        self.client.login(username="alice@example.com", password="StrongPass123!")
        self.category = Category.objects.create(user=self.user, name="Food", type_scope="Expense")

    def test_add_transaction_creates_record(self):
        response = self.client.post(
            reverse("finance:add_transaction"),
            {
                "amount": "12.50",
                "currency": "GBP",
                "type": "Expense",
                "category": str(self.category.id),
                "note": "Lunch",
            },
        )
        self.assertEqual(response.status_code, 302)
        tx = Transaction.objects.get(user=self.user)
        self.assertEqual(tx.original_amount, Decimal("12.50"))
        self.assertEqual(tx.amount_in_gbp, Decimal("12.50"))

    def test_delete_transaction_requires_post(self):
        tx = Transaction.objects.create(
            user=self.user,
            category=self.category,
            original_amount=Decimal("5.00"),
            currency="GBP",
            type="Expense",
            occurred_at=timezone.now(),
        )
        response = self.client.get(reverse("finance:delete_transaction", args=[tx.id]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Transaction.objects.filter(id=tx.id).exists())

    def test_delete_transaction_post_deletes(self):
        tx = Transaction.objects.create(
            user=self.user,
            category=self.category,
            original_amount=Decimal("8.00"),
            currency="GBP",
            type="Expense",
            occurred_at=timezone.now(),
        )
        response = self.client.post(reverse("finance:delete_transaction", args=[tx.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Transaction.objects.filter(id=tx.id).exists())

    def test_delete_category_requires_post(self):
        response = self.client.get(reverse("finance:delete_category", args=[self.category.id]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Category.objects.filter(id=self.category.id).exists())

    def test_delete_category_post_keeps_transactions(self):
        tx = Transaction.objects.create(
            user=self.user,
            category=self.category,
            original_amount=Decimal("11.00"),
            currency="GBP",
            type="Expense",
            occurred_at=timezone.now(),
        )
        response = self.client.post(reverse("finance:delete_category", args=[self.category.id]))
        self.assertEqual(response.status_code, 302)
        tx.refresh_from_db()
        self.assertIsNone(tx.category)

    def test_edit_transaction_owner_enforced(self):
        foreign_category = Category.objects.create(user=self.other_user, name="Travel", type_scope="Expense")
        foreign_tx = Transaction.objects.create(
            user=self.other_user,
            category=foreign_category,
            original_amount=Decimal("20.00"),
            currency="GBP",
            type="Expense",
            occurred_at=timezone.now(),
        )
        response = self.client.get(reverse("finance:edit_transaction", args=[foreign_tx.id]))
        self.assertEqual(response.status_code, 404)

    def test_transaction_list_paginates_and_preserves_query(self):
        for i in range(TRANSACTION_PAGE_SIZE + 1):
            Transaction.objects.create(
                user=self.user,
                category=self.category,
                original_amount=Decimal("3.00"),
                currency="GBP",
                type="Expense",
                note=f"coffee {i}",
                occurred_at=timezone.now() - timedelta(minutes=i),
            )
        response = self.client.get(reverse("finance:transaction_list"), {"q": "coffee", "page": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 2)
        self.assertEqual(response.context["query_string_without_page"], "q=coffee")


class FinanceApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="api@example.com",
            password="StrongPass123!",
            name="API User",
        )
        self.api_client = APIClient()

    def test_agent_api_requires_authentication(self):
        response = self.api_client.post(
            reverse("finance:agent_api"),
            {"amount": "3.50", "category": "Snacks"},
            format="json",
        )
        self.assertIn(response.status_code, [401, 403])

    def test_agent_api_creates_default_category_scope(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post(
            reverse("finance:agent_api"),
            {
                "amount": "3.50",
                "currency": "GBP",
                "type": "Expense",
                "category": "Snacks",
                "note": "chips",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        category = Category.objects.get(user=self.user, name="Snacks")
        self.assertEqual(category.type_scope, "Expense")

    def test_agent_api_normalizes_nonstandard_type(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post(
            reverse("finance:agent_api"),
            {
                "amount": "100",
                "currency": "GBP",
                "type": "Lotto",
                "category": "Other",
                "note": "won from lotto",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        tx = Transaction.objects.get(id=response.data["transaction_id"])
        self.assertEqual(tx.type, "Income")

    def test_chat_api_rejects_empty_query(self):
        self.api_client.force_authenticate(user=self.user)
        response = self.api_client.post(reverse("finance:chat_api"), {"query": ""}, format="json")
        self.assertEqual(response.status_code, 400)


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "finance-tests",
        }
    }
)
class FinanceRateAndOtpTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="otp@example.com",
            password="StrongPass123!",
            name="OTP User",
        )
        self.category = Category.objects.create(user=self.user, name="General", type_scope="Expense")

    @patch("finance.models.get_exchange_rate", return_value=Decimal("0.50"))
    def test_transaction_save_converts_non_gbp(self, mocked_rate):
        tx = Transaction.objects.create(
            user=self.user,
            category=self.category,
            original_amount=Decimal("10.00"),
            currency="USD",
            type="Expense",
            occurred_at=timezone.now(),
        )
        self.assertEqual(tx.amount_in_gbp, Decimal("5.00"))
        mocked_rate.assert_called_once_with("USD", "GBP")

    @patch("finance.utils.requests.get", side_effect=Exception("network down"))
    def test_exchange_rate_fallback_used_on_failure(self, _):
        self.assertEqual(get_exchange_rate("USD", "GBP"), Decimal("0.79"))

    @patch("finance.views.verify_turnstile", return_value=True)
    def test_send_code_has_rate_limit(self, _):
        first = self.client.post(
            reverse("finance:send_code"),
            {"email": "newuser@example.com", "cf_token": "ok"},
        )
        second = self.client.post(
            reverse("finance:send_code"),
            {"email": "newuser@example.com", "cf_token": "ok"},
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.json()["status"], "success")
        self.assertEqual(second.status_code, 429)
        self.assertEqual(second.json()["status"], "error")
        self.assertIn("Wait 60s", second.json()["message"])

    def test_send_code_requires_post(self):
        response = self.client.get(reverse("finance:send_code"))
        self.assertEqual(response.status_code, 405)

    @patch("finance.views.verify_turnstile", return_value=True)
    def test_send_code_persists_otp_audit_record(self, _):
        response = self.client.post(
            reverse("finance:send_code"),
            {"email": "audit@example.com", "cf_token": "ok"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        otp = UserEmailOTP.objects.get(email="audit@example.com", purpose="register")
        self.assertIsNotNone(otp.code_hash)
        self.assertIsNone(otp.used_at)

    @patch("finance.views.verify_turnstile", return_value=False)
    def test_send_code_rejects_failed_turnstile(self, _):
        response = self.client.post(
            reverse("finance:send_code"),
            {"email": "newuser@example.com", "cf_token": "bad"},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["status"], "error")
        self.assertIn("Security check failed", response.json()["message"])

    def test_register_rejects_weak_password(self):
        cache.set("finance:reg_otp:weak@example.com", "123456", timeout=600)
        response = self.client.post(
            reverse("finance:register"),
            {
                "email": "weak@example.com",
                "name": "Weak User",
                "password": "abcdef!",
                "code": "123456",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email="weak@example.com").exists())
        self.assertContains(response, "uppercase")

    def test_register_success_logs_user_in_and_redirects_dashboard(self):
        cache.set("finance:reg_otp:newuser@example.com", "123456", timeout=600)
        response = self.client.post(
            reverse("finance:register"),
            {
                "email": "newuser@example.com",
                "name": "New User",
                "password": "StrongPass123!",
                "code": "123456",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("finance:transaction_list"))
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())
        follow = self.client.get(reverse("finance:transaction_list"))
        self.assertEqual(follow.status_code, 200)

    def test_register_invalid_otp_keeps_entered_values(self):
        response = self.client.post(
            reverse("finance:register"),
            {
                "email": "keep@example.com",
                "name": "Keep User",
                "password": "StrongPass123!",
                "code": "111111",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="keep@example.com"')
        self.assertContains(response, 'value="Keep User"')
        self.assertContains(response, 'value="111111"')

    def test_risk_alert_created_for_abnormal_expense(self):
        Transaction.objects.create(
            user=self.user,
            category=self.category,
            original_amount=Decimal("10.00"),
            currency="GBP",
            type="Expense",
            occurred_at=timezone.now(),
            note="normal coffee",
        )
        tx = Transaction.objects.create(
            user=self.user,
            category=self.category,
            original_amount=Decimal("300.00"),
            currency="USD",
            type="Expense",
            occurred_at=timezone.now(),
            note="large unusual transfer",
        )
        alert = RiskAlert.objects.get(transaction=tx)
        self.assertIn(alert.risk_level, ["MEDIUM", "HIGH"])
        self.assertEqual(alert.status, "OPEN")


@override_settings(DEBUG=False)
class ErrorHandlingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="errors@example.com",
            password="StrongPass123!",
            name="Error User",
        )

    def test_unknown_api_path_returns_json_error(self):
        response = self.client.get(
            "/finance/api/not-exists/",
            HTTP_ACCEPT="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["status"], "error")
        self.assertEqual(response.json()["code"], "not_found")

    def test_unknown_html_path_redirects_to_login_with_message(self):
        response = self.client.get("/totally-missing-page/")
        self.assertEqual(response.status_code, 302)
        expected_next = reverse("finance:transaction_list")
        expected_login = reverse("login")
        self.assertEqual(response["Location"], f"{expected_login}?{urlencode({'next': expected_next})}")

    def test_unknown_html_path_for_logged_in_user_redirects_to_dashboard(self):
        self.client.login(username="errors@example.com", password="StrongPass123!")
        response = self.client.get("/another-missing-page/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("finance:transaction_list"))
