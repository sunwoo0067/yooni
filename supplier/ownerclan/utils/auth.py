# -*- coding: utf-8 -*-
"""
Utility functions for authenticating with the Ownerclan API.

This module provides a helper function `get_ownerclan_token` which issues a
POST request to the Ownerclan authentication endpoint and returns a JWT token.

Usage example
-------------
>>> from market.ownerclan.utils.auth import get_ownerclan_token
>>> token = get_ownerclan_token("b00679540", "ehdgod1101*")
>>> print(token)

The credentials (username & password) can also be supplied via environment
variables `OWNERCLAN_USERNAME` and `OWNERCLAN_PASSWORD` respectively so that
plain-text passwords don't have to be committed to source code.
"""
from __future__ import annotations

import os
from typing import Literal, TypedDict

import requests
from dotenv import load_dotenv

# Load environment variables from .env file when the module is imported
load_dotenv()

# Constants ------------------------------------------------------------------
PRODUCTION_AUTH_URL = "https://auth.ownerclan.com/auth"


Service = Literal["ownerclan"]
UserType = Literal["seller", "partner", "admin"]  # extend if necessary


class AuthResponse(TypedDict):
    """Expected fields returned by the Ownerclan auth API."""

    accessToken: str  # The issued JWT token
    tokenType: str  # e.g. "Bearer"
    expiresIn: int  # Seconds until expiry (30 days ≈ 2 592 000 seconds)


# Public API ------------------------------------------------------------------

def get_ownerclan_token(
    username: str | None = None,
    password: str | None = None,
    *,
    service: Service = "ownerclan",
    user_type: UserType = "seller",
    timeout: float | tuple[float, float] | None = 10,
) -> str:
    """Authenticate against the Ownerclan API and return a JWT access token.

    Parameters
    ----------
    username : str | None, optional
        The Ownerclan seller ID. If *None*, the function will look for the
        environment variable `OWNERCLAN_USERNAME`.
    password : str | None, optional
        The Ownerclan seller password. If *None*, the function will look for
        the environment variable `OWNERCLAN_PASSWORD`.
    service : Literal["ownerclan"], default "ownerclan"
        Service field required by the API – don't change unless the API
        specifies otherwise.
    user_type : Literal["seller", "partner", "admin"], default "seller"
        The type of user authenticating.
    timeout : float | tuple[float, float] | None, default 10
        How long to wait for the server to send data before giving up, in
        seconds. Passed directly to ``requests.post``.

    Returns
    -------
    str
        A JWT string that can be supplied in the ``Authorization`` header of
        subsequent API calls.

    Raises
    ------
    ValueError
        If credentials are missing.
    requests.HTTPError
        If the HTTP response status code is not ``200``.
    requests.RequestException
        For network-layer errors raised by *requests*.
    KeyError
        If the expected `accessToken` field is missing in the JSON response.
    """

    # ---------------------------------------------------------------------
    # Resolve credentials
    if username is None:
        username = os.getenv("OWNERCLAN_USERNAME")
    if password is None:
        password = os.getenv("OWNERCLAN_PASSWORD")

    if not username or not password:
        raise ValueError(
            "Ownerclan credentials are missing. Provide username/password "
            "arguments or set OWNERCLAN_USERNAME / OWNERCLAN_PASSWORD env vars."
        )

    # ---------------------------------------------------------------------
    # Build request payload
    payload = {
        "service": service,
        "userType": user_type,
        "username": username,
        "password": password,
    }

    auth_url = PRODUCTION_AUTH_URL

    response = requests.post(auth_url, json=payload, timeout=timeout)
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        # Enhance error with response text for easier debugging.
        raise requests.HTTPError(
            f"Ownerclan auth failed with status {response.status_code}: {response.text}"
        ) from exc

    # The API may return a raw JWT string with content-type text/plain, or a JSON
    # object containing `accessToken`. Handle both cases.
    content_type = response.headers.get("content-type", "").lower()
    if content_type.startswith("application/json"):
        json_data: AuthResponse = response.json()  # type: ignore[assignment]
        access_token = json_data.get("accessToken")
        if not access_token:
            raise KeyError("`accessToken` not found in Ownerclan auth response")
        return access_token

    # Fallback: treat entire response body as the JWT token.
    token_text = response.text.strip()
    if not token_text:
        raise ValueError("Empty response received from Ownerclan auth endpoint")
    return token_text


# Script / Debug ----------------------------------------------------------------
if __name__ == "__main__":
    """Allow running this file directly for ad-hoc token retrieval."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Obtain Ownerclan JWT token.")
    parser.add_argument("--username", "-u", help="Ownerclan seller ID")
    parser.add_argument("--password", "-p", help="Ownerclan seller password")


    args = parser.parse_args()

    try:
        token = get_ownerclan_token(
            username=args.username,
            password=args.password,
        )
        print(token)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
