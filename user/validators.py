import re

from django.core.exceptions import ValidationError


class PasswordComplexityValidator:
    def validate(self, password, user=None):
        if not re.search(r"[A-Z]", password):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password):
            raise ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r"[^A-Za-z0-9]", password):
            raise ValidationError("Password must contain at least one special character.")

    def get_help_text(self):
        return "Your password must include uppercase, lowercase, and at least one special character."
