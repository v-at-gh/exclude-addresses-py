
# `exclude-addresses.py`

## Overview

The `exclude-addresses.py` script is a utility for excluding specific IP networks or addresses from a target network. The script takes a target network and a list of addresses or networks to exclude, then calculates the resulting subnets after exclusion. The output can be formatted with optional separators, prefixes, and postfixes.

## Features

- Supports both IPv4 and IPv6 networks.
- Handles multiple exclusion addresses/networks in comma or space-separated format.
- Provides optional formatting of output using custom separators, prefixes, and postfixes.
- Detects and reports invalid, misfitting, or irrelevant addresses.
- Option to ignore invalid addresses and continue processing.

## Usage

```bash
./exclude-addresses.py <target_network> -a <addresses> [options]
```

### Positional Arguments

- `<target_network>`: The network from which addresses will be excluded. This must be a valid IP network (IPv4 or IPv6).

### Options

- `-a, --addresses <NETS>`: Comma or whitespace-separated list of addresses/networks to be excluded.
- `-s, --separator <SEP>`: Custom separator for the resulting network list. Default is a newline.
- `-p, --prefix <STR>`: Prefix to add before each resulting network in the output.
- `-P, --postfix <STR>`: Postfix to add after each resulting network in the output.
- `-i, --ignore`: Ignore invalid, misfitting, or irrelevant addresses and continue processing.

### Examples

#### Exclude a single network

```bash
./exclude-addresses.py 192.168.0.0/16 -a 192.168.1.0/24
```

#### Exclude multiple networks

Exclude Telegram networks from IPv4 address-space:
```bash
./exclude-addresses.py 0.0.0.0/0 -a '5.28.192.0/18 91.105.192.0/23 91.108.8.0/22 91.108.56.0/22 95.161.64.0/20 149.154.64.0/18 149.154.128.0/17'
```

#### Custom Output Formatting

Return a list of commands to set route for add subnetworks from `192.168.0.0/16` except `192.168.1.0/24`:
```bash
./exclude-addresses.py 192.168.0.0/16 -a 192.168.1.0/24 -p "ip route add " -P " via tun0"
```

### Error Handling

- If invalid or irrelevant addresses are provided, the script will terminate and provide an error message unless the `--ignore` flag is used.
  
### Exit Codes

- `0`: Success
- `1`: Invalid target network
- `2`: Invalid or irrelevant addresses provided

## Requirements

- Python 3.x
- `ipaddress` module (standard in Python 3.3+)

License

This script is open-source and available under the [MIT license](./LICENSE).
