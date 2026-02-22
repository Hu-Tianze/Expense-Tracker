import requests
from decimal import Decimal

def get_exchange_rate(from_currency, to_currency='GBP'):
    """
    使用 Frankfurter 开源 API 获取汇率 (无需 Key)
    """
    if from_currency == to_currency:
        return Decimal('1.0')
    
    try:
        # Frankfurter 是专门处理汇率的开源 API
        url = f"https://api.frankfurter.app/latest?from={from_currency}&to={to_currency}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            # 提取汇率并转为 Decimal 以保证金融计算精度
            rate = data['rates'].get(to_currency)
            if rate:
                return Decimal(str(rate))
        
    except Exception as e:
        print(f"汇率接口异常: {e}")
    
    # 兜底：如果网络断了，使用英国目前的大致汇率
    fallback = {
        'CNY': Decimal('0.11'),
        'USD': Decimal('0.79'),
        'EUR': Decimal('0.84')
    }
    return fallback.get(from_currency, Decimal('1.0'))