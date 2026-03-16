import requests
import json
from django.conf import settings
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from .models import Transaction
from django.db import transaction, models, DatabaseError
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
import logging
from .services import create_transaction
from .serializers import AgentTransactionRequestSerializer, ChatQuerySerializer
from .constants import (
    CURRENCY_CODES,
    AI_CHAT_TIMEOUT_SECONDS,
    ASSISTANT_NAME,
    ASSISTANT_NOTE_PREFIX_CHAT,
    ASSISTANT_NOTE_PREFIX_AGENT,
)

logger = logging.getLogger(__name__)


def api_error(message, status_code, code):
    return Response(
        {"status": "error", "code": code, "message": message},
        status=status_code,
    )


def serializer_error(serializer, code="validation_error"):
    # just return the first error, no need to dump everything at once
    field, errors = next(iter(serializer.errors.items()))
    msg = errors[0] if isinstance(errors, list) and errors else "Invalid input"
    return api_error(f"{field}: {msg}", 400, code)


class AgentTransactionAPI(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AgentTransactionRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return serializer_error(serializer, "invalid_payload")
        data = serializer.validated_data
        try:
            with transaction.atomic():
                cat_name = data.get('category', 'General').strip()
                new_tx = create_transaction(
                    user=request.user,
                    amount=data.get('amount'),
                    currency=data.get('currency', CURRENCY_CODES[0]),
                    tx_type=data.get('type', 'Expense'),
                    note=data.get('note', ''),
                    note_prefix=ASSISTANT_NOTE_PREFIX_AGENT,
                    occurred_at=data.get('date') or timezone.now(),
                    category_name=cat_name,
                    type_context=f"{data.get('note', '')} {cat_name}",
                )
                return Response({"status": "success", "transaction_id": new_tx.id})
        except ValueError:
            return api_error("Invalid amount format", 400, "invalid_amount")
        except DatabaseError:
            logger.exception("Agent transaction database error for user_id=%s", request.user.id)
            return api_error("Database write failed", 503, "database_unavailable")

class ChatAgentAPI(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return serializer_error(serializer, "invalid_payload")
        user_query = serializer.validated_data["query"]

        api_key = settings.GROQ_API_KEY
        
        if not api_key:
            return api_error("AI service is not configured", 503, "ai_not_configured")
        base_url = settings.AI_API_BASE_URL
        model_name = settings.AI_CHAT_MODEL

        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_txs = Transaction.objects.filter(user=request.user, occurred_at__gte=thirty_days_ago)
        stats = recent_txs.values('type').annotate(total=models.Sum('amount_in_gbp'))
        
        last_5 = recent_txs.order_by('-occurred_at')[:5]
        # give the model a bit of recent history so it picks the right category/type
        history_str = "\n".join([f"- {t.occurred_at.date()}: {t.amount_in_gbp} GBP ({t.category.name if t.category else 'General'})" for t in last_5])

        system_prompt = f"""
        You are a smart financial assistant. 
        User's 30-day memory stats: {list(stats)}.
        Recent history:
        {history_str}

        TASK:
        1. If recording a transaction, return JSON: {{"action": "record", "data": {{"amount": 10.5, "currency": "GBP", "category": "Food", "type": "Expense", "note": "..."}}}}
        2. If analyzing/chatting, return JSON: {{"action": "chat", "analysis": "Your reply here..."}}
        3. ALWAYS return valid JSON.
        """

        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            "response_format": {"type": "json_object"},
            "stream": False
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

        try:
            response = requests.post(base_url, json=payload, headers=headers, timeout=AI_CHAT_TIMEOUT_SECONDS)
            response.raise_for_status()
            res_json = response.json()
            ai_content = res_json['choices'][0]['message']['content']
            ai_data = json.loads(ai_content)

            if ai_data.get('action') == 'record':
                record_data = ai_data.get('data')
                # same service as the web form, so validation rules are identical
                with transaction.atomic():
                    cat_name = record_data.get('category', 'General')
                    new_tx = create_transaction(
                        user=request.user,
                        amount=record_data.get('amount'),
                        currency=record_data.get('currency', CURRENCY_CODES[0]),
                        tx_type=record_data.get('type', 'Expense'),
                        note=record_data.get('note', ''),
                        note_prefix=ASSISTANT_NOTE_PREFIX_CHAT,
                        occurred_at=record_data.get('date') or timezone.now(),
                        category_name=cat_name,
                        type_context=f"{user_query} {record_data.get('note', '')} {cat_name}",
                    )
                return Response({
                    "type": "record", 
                    "message": f"{ASSISTANT_NAME} recorded {new_tx.currency} {new_tx.original_amount} under {cat_name}.",
                    "transaction": {
                        "id": new_tx.id,
                        "note": (new_tx.note or "General Record"),
                        "category_name": new_tx.category.name if new_tx.category else "General",
                        "type": new_tx.type,
                        "currency": new_tx.currency,
                        "original_amount": f"{new_tx.original_amount:.2f}",
                        "amount_in_gbp": f"{new_tx.amount_in_gbp:.2f}",
                        "occurred_at_short": timezone.localtime(new_tx.occurred_at).strftime("%b %d, %H:%M"),
                        "occurred_at_full": timezone.localtime(new_tx.occurred_at).strftime("%b %d, %Y"),
                        "edit_url": reverse("finance:edit_transaction", args=[new_tx.id]),
                        "delete_url": reverse("finance:delete_transaction", args=[new_tx.id]),
                    },
                })
            else:
                return Response({
                    "type": "analysis", 
                    "message": ai_data.get('analysis', "I couldn't process that.")
                })

        except requests.RequestException:
            logger.exception("Chat agent upstream request failed for user_id=%s", request.user.id)
            return api_error("AI service is unavailable", 503, "ai_unavailable")
        except (KeyError, TypeError, json.JSONDecodeError, ValueError):
            logger.exception("Chat agent returned invalid payload for user_id=%s", request.user.id)
            return api_error("AI response could not be parsed", 502, "ai_invalid_payload")
        except DatabaseError:
            logger.exception("Chat agent database error for user_id=%s", request.user.id)
            return api_error("Database write failed", 503, "database_unavailable")


class DashboardStateAPI(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        base_items = Transaction.objects.filter(user=request.user).select_related("category")
        today = date.today()
        month_qs = base_items.filter(occurred_at__year=today.year, occurred_at__month=today.month)
        month_income = month_qs.filter(type='Income').aggregate(models.Sum('amount_in_gbp'))['amount_in_gbp__sum'] or Decimal("0")
        month_expense = month_qs.filter(type='Expense').aggregate(models.Sum('amount_in_gbp'))['amount_in_gbp__sum'] or Decimal("0")
        month_net = month_income - month_expense

        max_total = max(month_income, month_expense, Decimal("1"))
        expense_progress = float((month_expense / max_total) * Decimal("100")) if max_total > 0 else 0.0
        income_progress = float((month_income / max_total) * Decimal("100")) if max_total > 0 else 0.0

        expense_stats = month_qs.filter(type='Expense').values('category__name').annotate(total=models.Sum('amount_in_gbp'))
        chart_labels = [stat['category__name'] or 'General' for stat in expense_stats]
        chart_data = [float(stat['total']) for stat in expense_stats]

        total_count = base_items.count()

        return Response({
            "status": "success",
            "metrics": {
                "month_income": float(month_income),
                "month_expense": float(month_expense),
                "month_net": float(month_net),
                "expense_progress": round(expense_progress, 1),
                "income_progress": round(income_progress, 1),
            },
            "chart": {
                "labels": chart_labels,
                "data": chart_data,
            },
            "total_count": total_count,
        })
