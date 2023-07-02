#!/usr/bin/env python3

import keyring
import click
from getpass import getpass
from pkb_client.client import PKBClient, SUPPORTED_DNS_RECORD_TYPES
import tldextract
import ipaddress
import sys

SERVICE_ID = 'porkctl'

if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
    import keyrings.alt.file
    keyring.set_keyring(keyrings.alt.file.PlaintextKeyring())

@click.group()
def cli():
    pass


@cli.group()
def auth():
    pass


class LoginError(Exception):
    """Raised when there's an issue logging in"""
    pass


@auth.command()
def login():
    apikey = getpass('Enter your Porkbun API Key: ')
    apisecret = getpass('Enter your Porkbun API Secret: ')

    # Create a client with these credentials and attempt a ping
    client = PKBClient(apikey, apisecret)
    try:
        response = client.ping()
        # Check if response is a valid IP address
        try:
            ipaddress.ip_address(response)
        except ValueError:
            raise LoginError('Invalid credentials. Please try again.')
    except Exception as e:
        raise LoginError(f'Failed to verify credentials: {str(e)}')

    # If we get here, the ping was successful, so we can store the credentials
    keyring.set_password(SERVICE_ID, 'apikey', apikey)
    keyring.set_password(SERVICE_ID, 'apisecret', apisecret)
    print('Login successful!')


@auth.command()
def logout():
    keyring.delete_password(SERVICE_ID, 'apikey')
    keyring.delete_password(SERVICE_ID, 'apisecret')
    print('Logged out.')


@auth.command()
def status():
    if keyring.get_password(SERVICE_ID, 'apikey') is None or keyring.get_password(SERVICE_ID, 'apisecret') is None:
        print('You are not logged in.')
    else:
        print('You are logged in.')


@cli.group()
def dns():
    pass


def get_credentials():
    """Load the saved credentials from the keyring"""
    if not hasattr(get_credentials, '_cache'):
        get_credentials._cache = {}
    if 'apikey' not in get_credentials._cache:
        get_credentials._cache['apikey'] = keyring.get_password(
            SERVICE_ID, 'apikey')
    if 'apisecret' not in get_credentials._cache:
        get_credentials._cache['apisecret'] = keyring.get_password(
            SERVICE_ID, 'apisecret')
    if get_credentials._cache['apikey'] is None or get_credentials._cache['apisecret'] is None:
        raise LoginError('Please login first with: ./porkctl.py auth login')
    return get_credentials._cache['apikey'], get_credentials._cache['apisecret']


def create_client():
    try:
        apikey, apisecret = get_credentials()
        return PKBClient(apikey, apisecret)
    except Exception as e:
        print(e)


def extract_domain_subdomain(name):
    ext = tldextract.extract(name)
    subdomain = ext.subdomain
    domain = '.'.join(part for part in [ext.domain, ext.suffix] if part)
    return domain, subdomain


@dns.command()
@click.option('--name', prompt=True, type=str, help='Full Record name (FQDN)')
@click.option('--type', prompt=True, type=click.Choice(SUPPORTED_DNS_RECORD_TYPES), help='Record type')
@click.option('--data', prompt=True, type=str, help='Record data')
@click.option('--ttl', default=600, type=int, help='Record TTL (optional, defaults to 600 seconds)')
def create(name, type, data, ttl):
    """Create a new DNS record."""

    client = create_client()
    domain, subdomain = extract_domain_subdomain(name)

    # Call the DNS create API
    try:
        client.dns_create(
            domain=domain,
            name=subdomain,
            record_type=type,
            content=data,
            ttl=ttl
        )
        print(f'Successfully created DNS record: {name}')
    except Exception as e:
        print(f'Failed to create DNS record: {str(e)}')


@dns.command()
@click.argument('name', type=str)
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
            (record["id"] for record in records if record["name"] == name), None)

        if record_id is None:
            print(f"No DNS record found with name: {name}")
            return

        # Call the DNS delete API
        client.dns_delete(
            domain=domain,
            record_id=record_id
        )
        print(f'Successfully deleted DNS record with name: {name}')
    except Exception as e:
        print(f'Failed to delete DNS record: {str(e)}')


@dns.command()
@click.argument('name')
def list(name):
    """List all DNS records for a given domain."""

    client = create_client()

    # Call the DNS retrieve API
    try:
        records = client.dns_retrieve(domain=name)
        print(f'DNS records for {name}:')
        for record in records:
            print(f' - ID: {record["id"]}, Name: {record["name"]}, Type: {record["type"]}, Content: {record["content"]}, TTL: {record["ttl"]}, Priority: {record["prio"]}, Notes: {record["notes"]}')
    except Exception as e:
        print(f'Failed to list DNS records: {str(e)}')


@dns.command()
@click.option('--record_id', prompt=True, type=str,
              help='ID of the DNS record to update')
@click.option('--name', prompt=True, type=str, help='Full Record name (FQDN)')
@click.option('--type', prompt=True,
              type=click.Choice(SUPPORTED_DNS_RECORD_TYPES),
              help='Record type')
@click.option('--data', prompt=True, type=str, help='Record data')
@click.option('--ttl', default=600, type=int,
              help='Record TTL (optional, defaults to 600 seconds)')
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
            ttl=ttl
        )
        print(f'Successfully updated DNS record: {name}')
    except Exception as e:
        print(f'Failed to update DNS record: {str(e)}')


if __name__ == "__main__":
    cli()
