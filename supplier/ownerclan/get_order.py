# -*- coding: utf-8 -*-
"""
Fetches a single order from the Ownerclan API using GraphQL.

This script takes an order key as a command-line argument, obtains a JWT
token using the authentication utility, and then queries the Ownerclan
GraphQL endpoint for that specific order's details.

Usage:
------
# Ensure OWNERCLAN_USERNAME and OWNERCLAN_PASSWORD are set in your env
python get_order.py <ORDER_KEY>

# Or provide credentials directly to the auth utility if needed.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to sys.path to allow for absolute imports
# This makes the script runnable from any directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from supplier.ownerclan.utils.auth import get_ownerclan_token

# Constants ------------------------------------------------------------------
# Use the production endpoint for the GraphQL API.
GRAPHQL_URL = "https://api.ownerclan.com/v1/graphql"

# The GraphQL query as provided in the documentation.
# The '$' placeholder will be replaced with the actual order key.
ORDER_QUERY_TEMPLATE = """
query {
  order(key: "$") {
    key
    id
    products {
      quantity
      price
      shippingType
      itemKey
      itemOptionInfo {
        optionAttributes {
          name
          value
        }
        price
      }
      trackingNumber
      shippingCompanyCode
      shippedDate
      additionalAttributes {
        key
        value
      }
      taxFree
    }
    status
    shippingInfo {
      sender {
        name
        phoneNumber
        email
      }
      recipient {
        name
        phoneNumber
        destinationAddress {
          addr1
          addr2
          postalCode
        }
      }
      shippingFee
    }
    createdAt
    updatedAt
    note
    ordererNote
    sellerNote
    isBeingMediated
    adjustments {
      reason
      price
      taxFree
    }
    transactions {
      key
      id
      kind
      status
      amount {
        currency
        value
      }
      createdAt
      updatedAt
      closedAt
      note
    }
  }
}
"""


# Public API ------------------------------------------------------------------

def get_order(order_key: str, token: str) -> dict:
    """Queries the Ownerclan GraphQL API for a single order.

    Parameters
    ----------
    order_key : str
        The unique key of the order to retrieve (e.g., "2019000000000000000A").
    token : str
        The JWT authorization token.

    Returns
    -------
    dict
        The JSON response from the API containing the order data or errors.

    Raises
    ------
    requests.HTTPError
        If the HTTP response status code is not 200.
    requests.RequestException
        For network-layer errors raised by requests.
    """
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # Replace the placeholder with the actual order key
    query = ORDER_QUERY_TEMPLATE.replace("$", order_key)

    # The query can be sent in the body or as a URL parameter.
    # Sending as a URL parameter as shown in the docs.
    response = requests.get(GRAPHQL_URL, params={"query": query}, headers=headers, timeout=10)

    response.raise_for_status()
    return response.json()


# Script / Debug ----------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch a single order from Ownerclan.")
    parser.add_argument("order_key", help="The order key to look up.")

    args = parser.parse_args()

    try:
        print("1. Obtaining authentication token...")
        # Using the auth utility, which can pull credentials from env vars
        auth_token = get_ownerclan_token()
        print("   -> Token obtained successfully.")

        print(f"\n2. Fetching order data for key: {args.order_key}...")
        order_data = get_order(args.order_key, auth_token)
        print("   -> Data fetched successfully.")

        print("\n3. API Response:")
        # Pretty-print the JSON response
        print(json.dumps(order_data, indent=2, ensure_ascii=False))

    except Exception as exc:
        print(f"\nAn error occurred: {exc}", file=sys.stderr)
        sys.exit(1)
