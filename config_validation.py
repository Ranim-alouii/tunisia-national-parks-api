"""
Configuration Validation Module
Enhanced configuration validation with detailed error reporting and suggestions.
"""

import os
import re
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator, ValidationError
from pydantic_settings import BaseSettings


class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors."""
    def __init__(self, message: str, suggestions: List[str] = None):
        super().__init__(message)
        self.suggestions = suggestions or []


class EnvironmentConfig(BaseModel):
    """Enhanced environment configuration with validation."""

    # Database settings
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    db_host: str = Field(default="localhost", env="DB_HOST")
    db_port: int = Field(default=5432, env="DB_PORT", ge=1024, le=65535)
    db_name: str = Field(default="tunisia_parks", env="DB_NAME", min_length=1)
    db_user: Optional[str] = Field(default=None, env="DB_USER")
    db_password: Optional[str] = Field(default=None, env="DB_PASSWORD")

    # Security settings
    secret_key: str = Field(..., env="SECRET_KEY", min_length=32)
    algorithm: str = Field(default="HS256", env="ALGORITHM", regex="^(HS256|HS384|HS512)$")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES", ge=5, le=1440)

    # Admin settings
    admin_username: str = Field(..., env="ADMIN_USERNAME", min_length=3, max_length=50)
    admin_password: str = Field(..., env="ADMIN_PASSWORD", min_length=8)
    admin_full_name: str = Field(default="Administrator", env="ADMIN_FULL_NAME")

    # External API keys
    unsplash_access_key: Optional[str] = Field(default=None, env="UNSPLASH_ACCESS_KEY")
    google_places_api_key: Optional[str] = Field(default=None, env="GOOGLE_PLACES_API_KEY")
    newsapi_api_key: Optional[str] = Field(default=None, env="NEWSAPI_API_KEY")
    openweather_api_key: Optional[str] = Field(default=None, env="OPENWEATHER_API_KEY")

    # Email settings
    smtp_server: Optional[str] = Field(default=None, env="SMTP_SERVER")
    smtp_port: Optional[int] = Field(default=None, env="SMTP_PORT", ge=1, le=65535)
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")

    # Redis settings
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT", ge=1024, le=65535)
    redis_db: int = Field(default=0, env="REDIS_DB", ge=0, le=15)

    # CORS settings
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000", "http://localhost:8000"], env="CORS_ORIGINS")

    # Application settings
    environment: str = Field(default="development", env="ENVIRONMENT", regex="^(development|staging|production)$")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL", regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    # File upload settings
    max_upload_size: int = Field(default=10*1024*1024, env="MAX_UPLOAD_SIZE", ge=1024*1024, le=100*1024*1024)  # 1MB to 100MB
    allowed_extensions: List[str] = Field(default_factory=lambda: [".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf", ".mp4"], env="ALLOWED_EXTENSIONS")

    # Rate limiting
    rate_limit_requests: int = Field(default=60, env="RATE_LIMIT_REQUESTS", ge=10, le=1000)
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW", ge=1, le=3600)

    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long for security')
        return v

    @validator('admin_password')
    def validate_admin_password(cls, v):
        if len(v) < 8:
            raise ValueError('Admin password must be at least 8 characters long')

        # Check for complexity
        has_upper = re.search(r'[A-Z]', v)
        has_lower = re.search(r'[a-z]', v)
        has_digit = re.search(r'\d', v)
        has_special = re.search(r'[!@#$%^&*(),.?":{}|<>]', v)

        if not all([has_upper, has_lower, has_digit]):
            raise ValueError('Admin password must contain uppercase, lowercase, and numeric characters')

        return v

    @validator('cors_origins', each_item=True)
    def validate_cors_origins(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError(f'CORS origin must start with http:// or https://: {v}')
        return v

    @validator('allowed_extensions', each_item=True)
    def validate_extensions(cls, v):
        if not v.startswith('.'):
            raise ValueError(f'File extension must start with a dot: {v}')
        return v.lower()


class ConfigValidator:
    """Configuration validator with detailed error reporting."""

    def __init__(self):
        self.errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []

    def validate_config(self) -> EnvironmentConfig:
        """Validate the entire configuration and return validated config."""
        try:
            config = EnvironmentConfig()
            self._validate_external_services(config)
            self._validate_file_paths()
            self._validate_permissions()
            return config
        except ValidationError as e:
            self._handle_validation_error(e)
            raise ConfigValidationError(
                f"Configuration validation failed with {len(e.errors())} errors",
                self._generate_suggestions(e)
            )

    def _validate_external_services(self, config: EnvironmentConfig):
        """Validate external service configurations."""
        # Check API keys
        optional_apis = [
            ('unsplash_access_key', 'Unsplash API', 'https://unsplash.com/developers'),
            ('google_places_api_key', 'Google Places API', 'https://developers.google.com/maps/documentation/places/web-service/get-api-key'),
            ('newsapi_api_key', 'NewsAPI', 'https://newsapi.org/register'),
            ('openweather_api_key', 'OpenWeather API', 'https://openweathermap.org/api'),
        ]

        for field_name, service_name, signup_url in optional_apis:
            value = getattr(config, field_name)
            if not value:
                self.warnings.append({
                    'type': 'missing_api_key',
                    'field': field_name,
                    'service': service_name,
                    'signup_url': signup_url,
                    'message': f'{service_name} API key not configured - some features will be disabled'
                })

        # Check email configuration
        email_fields = ['smtp_server', 'smtp_username', 'smtp_password']
        email_configured = all(getattr(config, field) for field in email_fields)

        if not email_configured and any(getattr(config, field) for field in email_fields):
            self.errors.append({
                'type': 'incomplete_email_config',
                'message': 'Email configuration is incomplete. Either provide all SMTP settings or none.',
                'fields': email_fields
            })

    def _validate_file_paths(self):
        """Validate file system paths and permissions."""
        required_dirs = ['uploads', 'uploads/parks', 'uploads/species', 'static', 'templates']

        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                self.errors.append({
                    'type': 'missing_directory',
                    'path': dir_path,
                    'message': f'Required directory does not exist: {dir_path}'
                })
            elif not os.access(dir_path, os.W_OK):
                self.errors.append({
                    'type': 'permission_denied',
                    'path': dir_path,
                    'message': f'No write permission for directory: {dir_path}'
                })

    def _validate_permissions(self):
        """Validate system permissions and dependencies."""
        # Check if required ports are available (basic check)
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                result = s.connect_ex(('localhost', 6379))
                if result != 0:
                    self.warnings.append({
                        'type': 'service_unavailable',
                        'service': 'Redis',
                        'port': 6379,
                        'message': 'Redis is not running - caching will be disabled'
                    })
        except Exception:
            pass

    def _handle_validation_error(self, error: ValidationError):
        """Handle Pydantic validation errors."""
        for err in error.errors():
            self.errors.append({
                'type': 'validation_error',
                'field': '.'.join(str(loc) for loc in err['loc']),
                'message': err['msg'],
                'value': err.get('ctx', {}).get('given', 'N/A')
            })

    def _generate_suggestions(self, error: ValidationError) -> List[str]:
        """Generate helpful suggestions based on validation errors."""
        suggestions = []

        for err in error.errors():
            field = '.'.join(str(loc) for loc in err['loc'])

            if field == 'secret_key':
                suggestions.append("Generate a secure SECRET_KEY: python -c 'import secrets; print(secrets.token_hex(32))'")
            elif field == 'admin_password':
                suggestions.append("Create a strong admin password with uppercase, lowercase, and numbers")
            elif 'api_key' in field:
                suggestions.append(f"Get an API key for {field.replace('_api_key', '').title()} from their developer portal")
            elif field == 'cors_origins':
                suggestions.append("Add allowed origins in the format: http://localhost:3000,https://yourdomain.com")
            elif 'smtp' in field:
                suggestions.append("Configure SMTP settings for email functionality")

        if not suggestions:
            suggestions.append("Check the .env file for missing or incorrect configuration values")
            suggestions.append("Run the application with DEBUG=True to see more detailed error messages")

        return suggestions

    def get_report(self) -> Dict[str, Any]:
        """Get a comprehensive validation report."""
        return {
            'valid': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings)
        }


def validate_configuration() -> EnvironmentConfig:
    """
    Main function to validate configuration.
    Call this at application startup.
    """
    validator = ConfigValidator()

    try:
        config = validator.validate_config()
        report = validator.get_report()

        # Log warnings
        if report['warnings']:
            print("⚠️  Configuration Warnings:")
            for warning in report['warnings']:
                print(f"   - {warning['message']}")

        print(f"✅ Configuration validation successful ({report['warning_count']} warnings)")
        return config

    except ConfigValidationError as e:
        print("❌ Configuration validation failed:")
        for error in validator.errors:
            print(f"   - {error['message']}")

        print("\n💡 Suggestions:")
        for suggestion in e.suggestions:
            print(f"   - {suggestion}")

        raise


# Global configuration instance
config = None

def get_config() -> EnvironmentConfig:
    """Get the validated configuration instance."""
    global config
    if config is None:
        config = validate_configuration()
    return config


if __name__ == "__main__":
    # Allow running validation as a script
    try:
        config = validate_configuration()
        print("\n🎉 All configuration checks passed!")
        print(f"Environment: {config.environment}")
        print(f"Debug mode: {config.debug}")
    except ConfigValidationError:
        exit(1)
