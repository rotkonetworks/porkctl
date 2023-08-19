#!/usr/bin/env python3

import keyring
import click
from pkb_client.client import PKBClient, SUPPORTED_DNS_RECORD_TYPES
import tldextract
import ipaddress

SERVICE_ID = "porkctl"


@click.group(help="Porkbun CLI tool for managing authentication and DNS operations.")
def cli():
    pass


@cli.group(help="Commands related to authentication.")
def auth():
    pass


class LoginError(Exception):
    """Raised when there's an issue logging in"""

    pass


@auth.command(help="Log in using your Porkbun API Key and Secret.")
@click.option("--apikey", required=True, type=str, help="Porkbun API Key")
@click.option("--apisecret", required=True, type=str, help="Porkbun API Secret")
def login(apikey, apisecret):
    client = PKBClient(apikey, apisecret)
    try:
        response = client.ping()
        ipaddress.ip_address(response)
    except ValueError:
        raise LoginError("Invalid credentials. Please try again.")
    except Exception as e:
        raise LoginError(f"Failed to verify credentials: {e}")

    try:
        keyring.set_password(SERVICE_ID, "apikey", apikey)
        keyring.set_password(SERVICE_ID, "apisecret", apisecret)
        print("Login successful!")
    except keyring.errors.KeyringError as e:
        print(f"Error saving credentials: {e}")


@auth.command(help="Log out and remove stored credentials.")
def logout():
    try:
        keyring.delete_password(SERVICE_ID, "apikey")
        keyring.delete_password(SERVICE_ID, "apisecret")
        print("Logged out.")
    except keyring.errors.KeyringError as e:
        print(f"Error removing credentials: {e}")


@auth.command(help="Check the authentication status.")
def status():
    if (
        keyring.get_password(SERVICE_ID, "apikey") is None
        or keyring.get_password(SERVICE_ID, "apisecret") is None
    ):
        print("You are not logged in.")
    else:
        print("You are logged in.")


@cli.group(help="Commands related to DNS operations.")
def dns():
    pass


def get_credentials():
    try:
        return keyring.get_password(SERVICE_ID, "apikey"), keyring.get_password(
            SERVICE_ID, "apisecret"
        )
    except keyring.errors.KeyringError:
        raise LoginError("Error retrieving credentials.")


def create_client():
    apikey, apisecret = get_credentials()
    return PKBClient(apikey, apisecret)


def extract_domain_subdomain(name):
    ext = tldextract.extract(name)
    subdomain = ext.subdomain
    domain = ".".join(part for part in [ext.domain, ext.suffix] if part)
    return domain, subdomain


@dns.command(
    help="Create a new DNS record. For example:\n\n"
    "create --name 'example.com' --type 'A' --data '123.45.67.89'"
)
@click.option(
    "--name",
    required=True,
    type=str,
    help='Full Record name (FQDN). Example: "example.com"',
)
@click.option(
    "--type",
    required=True,
    type=click.Choice(SUPPORTED_DNS_RECORD_TYPES),
    help='Record type. Example: "A" for an IPv4 address.',
)
@click.option(
    "--data",
    required=True,
    type=str,
    help='Record data. Example: "123.45.67.89" for an A record.',
)
@click.option(
    "--ttl",
    default=600,
    type=int,
    help="Record TTL in seconds. Defaults to 600 seconds.",
)
def create(name, type, data, ttl):
    """Create a new DNS record."""
    client = create_client()
    domain, subdomain = extract_domain_subdomain(name)

    # Call the DNS create API
    try:
        client.dns_create(
            domain=domain, name=subdomain, record_type=type, content=data, ttl=ttl
        )
        print(f"Successfully created DNS record: {name}")
    except Exception as e:
        print(f"Failed to create DNS record: {str(e)}")


@dns.command(
    help="Delete a DNS record based on its full name (FQDN). Example usage:\n\n"
    "delete 'sub.example.com'"
)
@click.argument("name", type=str)
def delete(name):
    """Delete a DNS record.

    DOMAIN: Full Record name (FQDN) of the DNS record to delete
    """

    client = create_client()
    domain, _subdomain = extract_domain_subdomain(name)

    # Call the DNS retrieve API to get the record ID
    try:
        records = client.dns_retrieve(domain=domain)
        record_id = next(
            (record["id"]
             for record in records if record["name"] == name), None
        )

        if record_id is None:
            print(f"No DNS record found with name: {name}")
            return

        # Call the DNS delete API
        client.dns_delete(domain=domain, record_id=record_id)
        print(f"Successfully deleted DNS record with name: {name}")
    except Exception as e:
        print(f"Failed to delete DNS record: {str(e)}")


@dns.command(
    help="List all DNS records for a given domain. For example:\n\n"
    "list 'example.com'"
)
@click.argument("name")
def list(name):
    """List all DNS records for a given domain."""

    client = create_client()

    # Call the DNS retrieve API
    try:
        records = client.dns_retrieve(domain=name)
        print(f"DNS records for {name}:")
        for record in records:
            print(
                f' - ID: {record["id"]}, Name: {record["name"]}, Type: {record["type"]}, Content: {record["content"]}, TTL: {record["ttl"]}, Priority: {record["prio"]}, Notes: {record["notes"]}'
            )
    except Exception as e:
        print(f"Failed to list DNS records: {str(e)}")


@dns.command(
    help="Update an existing DNS record using its ID. Follow the prompts or provide all necessary details. "
    "Example:\n\n"
    "update --record_id 'abcd1234' --name 'sub.example.com' --type 'A' --data '123.45.67.89'"
)
@click.option(
    "--record_id",
    prompt=True,
    type=str,
    help='ID of the DNS record to update. Example: "abcd1234".',
)
@click.option(
    "--name",
    prompt=True,
    type=str,
    help='Full Record name (FQDN). Example: "sub.example.com".',
)
@click.option(
    "--type",
    prompt=True,
    type=click.Choice(SUPPORTED_DNS_RECORD_TYPES),
    help='Record type. Example: "A" for an IPv4 address.',
)
@click.option(
    "--data",
    prompt=True,
    type=str,
    help='Record data. Example: "123.45.67.89" for an A record.',
)
@click.option(
    "--ttl",
    default=600,
    type=int,
    help="Record TTL in seconds. Defaults to 600 seconds.",
)
def update(record_id, name, type, data, ttl):
    """Update a DNS record."""

    client = create_client()
    domain, subdomain = extract_domain_subdomain(name)

    # Call the DNS update API
    try:
        client.dns_edit(
            record_id=record_id,
            domain=domain,
            name=subdomain,
            record_type=type,
            content=data,
            ttl=ttl,
        )
        print(f"Successfully updated DNS record: {name}")
    except Exception as e:
        print(f"Failed to update DNS record: {str(e)}")


if __name__ == "__main__":
    cli()
