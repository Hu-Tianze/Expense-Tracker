from rest_framework import serializers


class AgentTransactionRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.ChoiceField(choices=["GBP", "CNY", "USD", "EUR"], required=False, default="GBP")
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
