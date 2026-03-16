from rest_framework import serializers
from .constants import CURRENCY_CODES


class AgentTransactionRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.ChoiceField(choices=CURRENCY_CODES, required=False, default=CURRENCY_CODES[0])
    type = serializers.CharField(required=False, allow_blank=True, default="Expense")
    category = serializers.CharField(required=False, allow_blank=True, default="General")
    note = serializers.CharField(required=False, allow_blank=True, default="")
    date = serializers.DateTimeField(required=False, allow_null=True)


class ChatQuerySerializer(serializers.Serializer):
    query = serializers.CharField()

    def validate_query(self, value):
        query = (value or "").strip()
        if not query:
            raise serializers.ValidationError("Query cannot be empty")
        return query
