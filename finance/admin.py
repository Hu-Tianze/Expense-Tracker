from django.contrib import admin
from .models import Category, Transaction, AuditLog

# 1. 优化 Category 注册：能看到是谁创建的分类
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'type_scope')
    list_filter = ('user', 'type_scope')
    search_fields = ('name',)

# 2. 增强 Transaction 注册
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    # 列表页显示的列
    list_display = ('occurred_at', 'user', 'type', 'category', 'original_amount', 'currency', 'amount_in_gbp')
    # 右侧过滤器：增加用户筛选
    list_filter = ('user', 'type', 'currency', 'occurred_at')
    # 搜索框：支持按备注和用户邮箱搜索（工业级标配）
    search_fields = ('note', 'user__email')
    # 只读字段
    readonly_fields = ('amount_in_gbp',)
    # 排序：默认按最新时间排序
    ordering = ('-occurred_at',)

# 3. 审计日志（保持你的优秀代码，增加了一点点优化）
@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'action', 'resource_type', 'description')
    list_filter = ('action', 'resource_type', 'created_at', 'user')
    search_fields = ('description', 'user__email')
    readonly_fields = ('user', 'action', 'resource_type', 'description', 'ip_address', 'created_at')

    # 工业级防护：禁止添加、删除和修改日志，只能查看
    def has_add_permission(self, request): return False
    def has_delete_permission(self, request, obj=None): return False
    def has_change_permission(self, request, obj=None): return False