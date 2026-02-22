from django.db import models
from decimal import Decimal
# Create your models here.
from django.db import models
from django.conf import settings
from .utils import get_exchange_rate
# 表 3: categories (账目分类)
class Category(models.Model):
    # 连接 users 表，使用 settings.AUTH_USER_MODEL 保证兼容性
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='categories'
    )
    
    name = models.CharField(max_length=100)
    # type_scope: 收入/支出
    type_scope = models.CharField(max_length=20) 
    # sort_order: 分类在界面上显示的顺序
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # 文档约束：Unique(user_id, name) - 同一个用户下分类名不能重复
        unique_together = ('user', 'name')
        verbose_name = "账目分类"
        verbose_name_plural = "账目分类"

    def __str__(self):
        return f"{self.name} ({self.type_scope})"

# 表 4: transactions (交易记录)
class Transaction(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='transactions'
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='transactions'
    )
    
    # 货币支持
    CURRENCY_CHOICES = [
        ('GBP', 'British Pound (£)'),
        ('CNY', 'Chinese Yuan (¥)'),
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
    ]
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='GBP')
    
    # 金额逻辑
    original_amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="输入金额")
    amount_in_gbp = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="结算金额(GBP)",null=True, blank=True, editable=False)
    
    type = models.CharField(max_length=20) # 收入/支出
    occurred_at = models.DateTimeField(verbose_name="发生时间")
    note = models.TextField(blank=True, null=True, verbose_name="备注")
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # 1. 索引优化：让查询 user 的账单速度飞快
            indexes = [
                models.Index(fields=['user', 'occurred_at']),
                models.Index(fields=['user', 'category', 'occurred_at']),
            ]
        # 2. 约束：从数据库底层保证金额永远 > 0，不怕脏数据
            constraints = [
                models.CheckConstraint(condition=models.Q(original_amount__gt=0), name='amount_gt_0'),
            ]
        # 3. 后台显示名称（更正了拼写）
            verbose_name = "Transaction record"
            verbose_name_plural = "Transaction records"
    # 修改 models.py 里的 save 方法


    def save(self, *args, **kwargs):
        orig = Decimal(str(self.original_amount))
        print(f"--- 开始保存: 币种={self.currency}, 金额={orig} ---") # 加这行

        if self.currency == 'GBP':
            self.amount_in_gbp = orig
        else:
            rate = get_exchange_rate(self.currency, 'GBP')
            print(f"--- 拿到汇率: {rate} ---") # 加这行
            self.amount_in_gbp = orig * rate
            print(f"--- 计算出的英镑金额: {self.amount_in_gbp} ---") # 加这行

        super().save(*args, **kwargs)
        print("Saved") 
            
    def __str__(self):
        return f"{self.occurred_at.date()} - {self.currency} {self.original_amount}"
    
    # ... 在 Transaction 类的代码下面添加 ...

class EmailOTP(models.Model):
    email = models.EmailField(verbose_name="Email Address")
    otp_code = models.CharField(max_length=6, verbose_name="OTP Code")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        verbose_name = "Email OTP"
        verbose_name_plural = "Email OTPs"
        indexes = [
            models.Index(fields=['email', 'created_at']),
        ]

    def __str__(self):
        return f"{self.email} - {self.otp_code} at {self.created_at}"
    
    
# finance/models.py

class AuditLog(models.Model):
    # 操作类型定义
    ACTION_CHOICES = [
        ('LOGIN', 'User Login'),
        ('CREATE', 'Create Record'),
        ('UPDATE', 'Update Record'),
        ('DELETE', 'Delete Record'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='audit_logs')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    resource_type = models.CharField(max_length=50)  # 例如 "Transaction" 或 "Category"
    description = models.TextField()                 # 详细描述，如 "Deleted transaction #105"
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.created_at}"