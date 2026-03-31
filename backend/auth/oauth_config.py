"""
OAuth provider configuration.

Supports Google OAuth and generic OIDC (Okta) for @intercom.io login.
All settings are optional — when not configured, auth is disabled.
"""

import os
from dataclasses import dataclass
from functools import lru_cache


GOOGLE_ENDPOINTS = {
    "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth",
    "token_url": "https://oauth2.googleapis.com/token",
    "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
    "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
    "scopes": ["openid", "email", "profile"],
}


def _okta_endpoints(issuer: str) -> dict:
    """Build Okta OIDC endpoints from issuer URL."""
    base = issuer.rstrip("/")
    return {
        "authorization_url": f"{base}/v1/authorize",
        "token_url": f"{base}/v1/token",
        "userinfo_url": f"{base}/v1/userinfo",
        "jwks_uri": f"{base}/v1/keys",
        "scopes": ["openid", "email", "profile"],
    }


@dataclass(frozen=True)
class OAuthConfig:
    """Resolved OAuth configuration from environment variables."""

    provider: str
    client_id: str
    client_secret: str
    redirect_uri: str
    allowed_email_domains: tuple[str, ...]
    auth_enabled: bool
    okta_issuer: str

    @property
    def is_configured(self) -> bool:
        """True when OAuth has minimum required settings to function."""
        return bool(self.auth_enabled and self.client_id and self.client_secret)

    @property
    def provider_endpoints(self) -> dict:
        """Resolved OIDC endpoints for the active provider."""
        if self.provider == "okta":
            if not self.okta_issuer:
                raise ValueError("OKTA_ISSUER is required when provider is okta")
            return _okta_endpoints(self.okta_issuer)
        return dict(GOOGLE_ENDPOINTS)

    def is_email_allowed(self, email: str) -> bool:
        """Check if an email belongs to an allowed domain."""
        if not email or "@" not in email:
            return False
        domain = email.rsplit("@", 1)[1].lower()
        return domain in self.allowed_email_domains

    @classmethod
    def from_env(cls) -> "OAuthConfig":
        """Load configuration from environment variables.

        Reads generic OAUTH_* vars with fallback to provider-specific
        vars (GOOGLE_CLIENT_ID, OKTA_CLIENT_ID) for backward compat.
        """
        provider = os.environ.get(
            "OAUTH_PROVIDER", os.environ.get("AUTH_PROVIDER", "google")
        ).lower()

        if provider == "okta":
            client_id = os.environ.get(
                "OAUTH_CLIENT_ID", os.environ.get("OKTA_CLIENT_ID", "")
            )
            client_secret = os.environ.get(
                "OAUTH_CLIENT_SECRET", os.environ.get("OKTA_CLIENT_SECRET", "")
            )
        else:
            client_id = os.environ.get(
                "OAUTH_CLIENT_ID", os.environ.get("GOOGLE_CLIENT_ID", "")
            )
            client_secret = os.environ.get(
                "OAUTH_CLIENT_SECRET", os.environ.get("GOOGLE_CLIENT_SECRET", "")
            )

        domains_raw = os.environ.get(
            "ALLOWED_EMAIL_DOMAINS",
            os.environ.get("AUTH_ALLOWED_DOMAIN", "intercom.io"),
        )
        domains = tuple(
            d.strip().lower() for d in domains_raw.split(",") if d.strip()
        )

        return cls(
            provider=provider,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=os.environ.get(
                "OAUTH_REDIRECT_URI", "http://localhost:5001/auth/callback"
            ),
            allowed_email_domains=domains,
            auth_enabled=os.environ.get("AUTH_ENABLED", "false").lower() == "true",
            okta_issuer=os.environ.get("OKTA_ISSUER", ""),
        )


@lru_cache(maxsize=1)
def get_oauth_config() -> OAuthConfig:
    """Get cached OAuth configuration singleton."""
    return OAuthConfig.from_env()
