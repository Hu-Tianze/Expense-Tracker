import requests
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from .models import Transaction, Category
from decimal import Decimal, InvalidOperation
from django.db import transaction, models
from django.utils import timezone
from datetime import timedelta
import os
# ================= 1. 基础记账接口 (供 Agent 脚本直接调用) =================

class AgentTransactionAPI(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        try:
            with transaction.atomic():
                amount_val = data.get('amount')
                if not amount_val:
                    return Response({"status": "error", "message": "Amount is required"}, status=400)
                
                amount = Decimal(str(amount_val))
                cat_name = data.get('category', 'General').strip()
                category, _ = Category.objects.get_or_create(user=request.user, name=cat_name)

                new_tx = Transaction.objects.create(
                    user=request.user,
                    category=category,
                    original_amount=amount,
                    currency=data.get('currency', 'GBP'),
                    type=data.get('type', 'Expense'),
                    note=f"[AI Agent] {data.get('note', '')}",
                    occurred_at=data.get('date') or timezone.now()
                )
                return Response({"status": "success", "transaction_id": new_tx.id})
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=500)

# ================= 2. 高级对话接口 (云端 AI 驱动) =================

class ChatAgentAPI(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user_query = request.data.get('query', '').strip()
        if not user_query:
            return Response({"error": "Query cannot be empty"}, status=400)

        API_KEY = os.getenv("GROQ_API_KEY") 
        
        if not API_KEY:
            return Response({"error": "GROQ_API_KEY not found in environment variables"}, status=500)
        BASE_URL = "https://api.groq.com/openai/v1/chat/completions" 
        MODEL_NAME = "llama-3.1-8b-instant" # 这个模型解析记账非常稳

        # 1. 调取 30 天记忆：构建财务背景
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_txs = Transaction.objects.filter(user=request.user, occurred_at__gte=thirty_days_ago)
        stats = recent_txs.values('type').annotate(total=models.Sum('amount_in_gbp'))
        
        # 获取最近 5 笔交易增强感知
        last_5 = recent_txs.order_by('-occurred_at')[:5]
        history_str = "\n".join([f"- {t.occurred_at.date()}: {t.amount_in_gbp} GBP ({t.category.name if t.category else 'General'})" for t in last_5])

        # 2. 构造 System Prompt
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

        # 3. 发起请求
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
            res_json = response.json()
            print(f"📡 Cloud API Response: {res_json}")
            ai_content = res_json['choices'][0]['message']['content']
            ai_data = json.loads(ai_content)

            # 4. 执行分支逻辑
            if ai_data.get('action') == 'record':
                record_data = ai_data.get('data')
                with transaction.atomic():
                    cat_name = record_data.get('category', 'General')
                    category, _ = Category.objects.get_or_create(user=request.user, name=cat_name)
                    
                    # --- 这里是修复后的创建逻辑 ---
                    new_tx = Transaction.objects.create(
                        user=request.user,
                        category=category,
                        original_amount=Decimal(str(record_data.get('amount'))),
                        currency=record_data.get('currency', 'GBP'),
                        type=record_data.get('type', 'Expense'),
                        note=f"[AI Chat] {record_data.get('note', '')}",
                        # 核心修复：如果 AI 没传具体日期，就用服务器当前时间
                        occurred_at=record_data.get('date') or timezone.now() 
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

        except Exception as e:
            # 在终端打印出具体的错误，方便你调试
            print(f"❌ ERROR: {str(e)}") 
            return Response({"error": f"Internal Server Error: {str(e)}"}, status=500)