# PorkCtl

`PorkCtl` is a command-line tool for interacting with the Porkbun API to manage DNS records.

## Prerequisites

Before you start, you will need to have Python 3 installed on your machine. 

You will also need to install the required dependencies. You can do this by running the following command in the terminal:

```
pip install -r requirements.txt
```

If you wish to contribute to the project, install the development dependencies as well:

```
pip install -r dev-requirements.txt
```

## Usage

First, you'll need to authenticate. Run:

```
./porkctl auth login
```

You'll be prompted to enter your Porkbun API Key and Secret. These are stored securely and are used for subsequent commands.

To log out (and delete the stored API Key and Secret), run:

```
./porkctl auth logout
```

You can check your authentication status with:

```
./porkctl auth status
```

### DNS Records

#### List DNS Records

To list all DNS records for a domain, use:

```
./porkctl dns list example.com
```

Replace `example.com` with your domain.

#### Create DNS Record

To create a new DNS record, use:

```
./porkctl dns create --name record.example.com --type A --data 192.0.2.1
```

In this example, `record.example.com` is the full record name (FQDN), `A` is the record type and `192.0.2.1` is the record data (for an A record, this would be an IPv4 address). You can optionally specify a TTL (Time To Live) in seconds using `--ttl`; if you don't, it defaults to 600 seconds.

#### Delete DNS Record

To delete a DNS record, use:

```
./porkctl dns delete record.example.com
```

Replace `record.example.com` with the FQDN of the record you wish to delete.

#### Update DNS Record

To update a DNS record, use:

```
./porkctl dns update --record_id id --name record.example.com --type A --data 192.0.2.2
```

In this example, `id` is the ID of the DNS record you want to update, `record.example.com` is the full record name (FQDN), `A` is the record type and `192.0.2.2` is the new record data. Again, you can optionally specify a TTL using `--ttl`.

## Building a Binary

If you wish to build a standalone executable for this tool, you can use PyInstaller:

```
pyinstaller --onefile porkctl.py
```

This will create a single executable file in the `dist/` directory. This executable can be run without requiring a Python interpreter or any dependencies to be installed on the machine. Note that this executable will be specific to the platform and architecture that you build it on.

