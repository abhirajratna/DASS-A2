import os
from dataclasses import dataclass
from typing import Any

import pytest
import requests


@dataclass
class ApiConfig:
    base_url: str
    roll_number: str
    default_user_id: int
    secondary_user_id: int
    timeout: int


class ApiClient:
    def __init__(self, config: ApiConfig):
        self.config = config

    def _url(self, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        base = self.config.base_url.rstrip("/")
        suffix = path if path.startswith("/") else f"/{path}"
        return f"{base}{suffix}"

    def request(
        self,
        method: str,
        path: str,
        *,
        user_id: int | None = None,
        roll_number: str | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        final_headers: dict[str, str] = {"X-Roll-Number": roll_number or self.config.roll_number}
        if user_id is not None:
            final_headers["X-User-ID"] = str(user_id)
        if headers:
            final_headers.update(headers)
        return requests.request(
            method=method.upper(),
            url=self._url(path),
            headers=final_headers,
            json=json,
            params=params,
            timeout=self.config.timeout,
        )

    def clear_cart(self, user_id: int) -> requests.Response:
        return self.request("DELETE", "/cart/clear", user_id=user_id)

    def remove_coupon(self, user_id: int) -> requests.Response:
        return self.request("POST", "/coupon/remove", user_id=user_id)


@pytest.fixture(scope="session")
def api_config() -> ApiConfig:
    return ApiConfig(
        base_url=os.getenv("QUICKCART_BASE_URL", "http://localhost:8080/api/v1"),
        roll_number=os.getenv("QUICKCART_ROLL", "2024101018"),
        default_user_id=int(os.getenv("QUICKCART_USER_ID", "1")),
        secondary_user_id=int(os.getenv("QUICKCART_SECONDARY_USER_ID", "10")),
        timeout=int(os.getenv("QUICKCART_TIMEOUT", "10")),
    )


@pytest.fixture(scope="session")
def api(api_config: ApiConfig) -> ApiClient:
    return ApiClient(api_config)


@pytest.fixture(scope="session", autouse=True)
def ensure_server_reachable(api: ApiClient):
    try:
        resp = api.request("GET", "/admin/users", user_id=None)
        if resp.status_code not in {200, 401, 400}:
            pytest.skip(f"QuickCart server not ready (status={resp.status_code})")
    except requests.RequestException as exc:
        pytest.skip(f"QuickCart server not reachable: {exc}")


@pytest.fixture
def user_id(api_config: ApiConfig) -> int:
    return api_config.default_user_id


@pytest.fixture
def secondary_user_id(api: ApiClient, api_config: ApiConfig, user_id: int) -> int:
    probe = api.request("GET", "/profile", user_id=api_config.secondary_user_id)
    if probe.status_code == 200:
        return api_config.secondary_user_id
    return user_id


@pytest.fixture
def active_product_id(api: ApiClient, user_id: int) -> int:
    resp = api.request("GET", "/products", user_id=user_id)
    assert resp.status_code == 200
    body = resp.json()
    products = body.get("products", []) if isinstance(body, dict) else []
    if not products:
        pytest.skip("No active products available for cart/checkout tests")
    return int(products[0]["product_id"])


@pytest.fixture
def second_active_product_id(api: ApiClient, user_id: int, active_product_id: int) -> int:
    resp = api.request("GET", "/products", user_id=user_id)
    assert resp.status_code == 200
    products = resp.json().get("products", [])
    for product in products:
        product_id = int(product["product_id"])
        if product_id != active_product_id:
            return product_id
    return active_product_id


@pytest.fixture
def clean_cart(api: ApiClient, user_id: int):
    api.clear_cart(user_id)
    api.remove_coupon(user_id)
    yield
    api.clear_cart(user_id)
    api.remove_coupon(user_id)


@pytest.fixture
def clean_secondary_cart(api: ApiClient, secondary_user_id: int):
    api.clear_cart(secondary_user_id)
    api.remove_coupon(secondary_user_id)
    yield
    api.clear_cart(secondary_user_id)
    api.remove_coupon(secondary_user_id)
