import requests
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework import serializers
from .models import Transaction
from django.db import transaction, models
from django.utils import timezone
from datetime import timedelta
import os
import logging
from .services import create_transaction
from .serializers import AgentTransactionRequestSerializer, ChatQuerySerializer

logger = logging.getLogger(__name__)


def api_error(message, status_code, code):
    return Response(
        {"status": "error", "code": code, "message": message},
        status=status_code,
    )


def serializer_error(serializer, code="validation_error"):
    # Return first field-level error in a compact, client-friendly format.
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
                    currency=data.get('currency', 'GBP'),
                    tx_type=data.get('type', 'Expense'),
                    note=data.get('note', ''),
                    note_prefix='[AI Agent] ',
                    occurred_at=data.get('date') or timezone.now(),
                    category_name=cat_name,
                    type_context=f"{data.get('note', '')} {cat_name}",
                )
                return Response({"status": "success", "transaction_id": new_tx.id})
        except ValueError:
            return api_error("Invalid amount format", 400, "invalid_amount")
        except Exception:
            logger.exception("Agent transaction create failed for user_id=%s", request.user.id)
            return api_error("Internal server error", 500, "internal_error")

class ChatAgentAPI(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChatQuerySerializer(data=request.data)
        if not serializer.is_valid():
            return serializer_error(serializer, "invalid_payload")
        user_query = serializer.validated_data["query"]

        API_KEY = os.getenv("GROQ_API_KEY") 
        
        if not API_KEY:
            return api_error("AI service is not configured", 500, "ai_not_configured")
        BASE_URL = "https://api.groq.com/openai/v1/chat/completions" 
        MODEL_NAME = "llama-3.1-8b-instant"

        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_txs = Transaction.objects.filter(user=request.user, occurred_at__gte=thirty_days_ago)
        stats = recent_txs.values('type').annotate(total=models.Sum('amount_in_gbp'))
        
        last_5 = recent_txs.order_by('-occurred_at')[:5]
        # Inject lightweight recent context to improve transaction parsing consistency.
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
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            "response_format": {"type": "json_object"},
            "stream": False
        }
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}

        try:
            response = requests.post(BASE_URL, json=payload, headers=headers, timeout=20)
            response.raise_for_status()
            res_json = response.json()
            ai_content = res_json['choices'][0]['message']['content']
            ai_data = json.loads(ai_content)

            if ai_data.get('action') == 'record':
                record_data = ai_data.get('data')
                # Persist through shared service to reuse canonical validation/normalization.
                with transaction.atomic():
                    cat_name = record_data.get('category', 'General')
                    new_tx = create_transaction(
                        user=request.user,
                        amount=record_data.get('amount'),
                        currency=record_data.get('currency', 'GBP'),
                        tx_type=record_data.get('type', 'Expense'),
                        note=record_data.get('note', ''),
                        note_prefix='[AI Chat] ',
                        occurred_at=record_data.get('date') or timezone.now(),
                        category_name=cat_name,
                        type_context=f"{user_query} {record_data.get('note', '')} {cat_name}",
                    )
                return Response({
                    "type": "record", 
                    "message": f"Got it! I've recorded £{new_tx.original_amount} under {cat_name}."
                })
            else:
                return Response({
                    "type": "analysis", 
                    "message": ai_data.get('analysis', "I couldn't process that.")
                })

        except Exception:
            logger.exception("Chat agent failed for user_id=%s", request.user.id)
            return api_error("Internal server error", 500, "internal_error")
