"""
Custom exceptions for the Data Quality Framework
"""


class ValidationError(Exception):
    """Raised when data validation fails"""

    def __init__(self, message: str, validation_errors: dict = None):
        self.message = message
        self.validation_errors = validation_errors or {}
        super().__init__(self.message)

    def __str__(self):
        if self.validation_errors:
            return f"{self.message}\nDetails: {self.validation_errors}"
        return self.message


class ConfigError(Exception):
    """Raised when configuration is invalid"""

    pass


class RuleDefinitionError(Exception):
    """Raised when a validation rule is incorrectly defined"""

    pass
