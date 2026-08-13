from __future__ import annotations

import base64
import time
import uuid
from dataclasses import dataclass

import httpx

from app.domain.errors import ConfigurationError, ExternalProviderUnavailableError


@dataclass(slots=True)
class GigaChatToken:
    access_token: str
    expires_at: int


class GigaChatAuthClient:
    """OAuth helper for GigaChat REST API.

    GigaChat issues short-lived access tokens via POST /api/v2/oauth. The request
    requires a Basic authorization key and an RqUID UUID header.
    """

    def __init__(
        self,
        auth_url: str,
        scope: str,
        authorization_key: str | None = None,
        client_id: str | None = None,
        client_secret: str | None = None,
        verify_ssl: bool = True,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.auth_url = auth_url
        self.scope = scope
        self.authorization = self._build_authorization_header(
            authorization_key=authorization_key,
            client_id=client_id,
            client_secret=client_secret,
        )
        self.verify_ssl = verify_ssl
        self.http_client = http_client
        self._token: GigaChatToken | None = None

    async def get_access_token(self) -> str:
        now = int(time.time() * 1000)
        if self._token and self._token.expires_at - 60_000 > now:
            return self._token.access_token

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': self.authorization,
        }
        data = {'scope': self.scope}

        try:
            if self.http_client is not None:
                response = await self.http_client.post(self.auth_url, headers=headers, data=data)
            else:
                async with httpx.AsyncClient(timeout=30, verify=self.verify_ssl) as client:
                    response = await client.post(self.auth_url, headers=headers, data=data)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            raise ExternalProviderUnavailableError(f'Failed to get GigaChat access token: {exc}') from exc

        access_token = payload.get('access_token')
        expires_at = payload.get('expires_at')
        if not access_token or not expires_at:
            raise ExternalProviderUnavailableError('Invalid GigaChat OAuth response: access_token or expires_at is missing')

        self._token = GigaChatToken(access_token=str(access_token), expires_at=int(expires_at))
        return self._token.access_token

    @staticmethod
    def _build_authorization_header(
        authorization_key: str | None,
        client_id: str | None,
        client_secret: str | None,
    ) -> str:
        if authorization_key:
            return authorization_key if authorization_key.startswith('Basic ') else f'Basic {authorization_key}'

        if client_id and client_secret:
            raw = f'{client_id}:{client_secret}'.encode('utf-8')
            encoded = base64.b64encode(raw).decode('ascii')
            return f'Basic {encoded}'

        raise ConfigurationError(
            'GigaChat credentials are required: set GIGACHAT_AUTHORIZATION_KEY or both '
            'GIGACHAT_CLIENT_ID and GIGACHAT_CLIENT_SECRET'
        )
