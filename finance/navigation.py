from django.urls import reverse


def get_site_search_items():
    dashboard_url = reverse("finance:transaction_list")
    profile_url = reverse("finance:profile")
    export_url = reverse("finance:export_csv")
    return (
        {"label": "Dashboard", "value": "dashboard", "target": dashboard_url},
        {"label": "Transactions", "value": "transactions", "target": f"{dashboard_url}#recent-transactions"},
        {"label": "Analytics", "value": "analytics", "target": f"{dashboard_url}#kpi-column"},
        {"label": "Profile", "value": "profile", "target": profile_url},
        {"label": "Nickname", "value": "nickname", "target": f"{profile_url}#profileForm"},
        {"label": "Delete Account", "value": "delete account", "target": f"{profile_url}#danger-zone"},
        {"label": "Change Password", "value": "change password", "target": f"{profile_url}#security-section"},
        {"label": "Export CSV", "value": "export csv", "target": export_url},
        {"label": "AI Assistant", "value": "assistant", "target": f"{dashboard_url}#ai-chat-wrapper"},
        {"label": "Add Transaction", "value": "add transaction", "target": f"{dashboard_url}#recent-transactions"},
    )
