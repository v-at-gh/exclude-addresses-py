#!/usr/bin/env python3

import sys
from argparse import ArgumentParser, Namespace
from typing import Iterator, List, Optional, NoReturn, Union
from ipaddress import (
    IPv4Network, IPv6Network, 
    ip_address, ip_network,
    collapse_addresses
)


ARGHELP_NETWORK = "The network from which we exclude addresses"
ARGHELP_ADDRESSES = "comma or whitespace separated addresses of hosts and/or networks to be excluded"
ARGHELP_SEPARATOR = "separator for the list of resulting networks. Default is the new line"
ARGHELP_PREFIX = "prefix to put before each resulting network, for example `ip route add `"
ARGHELP_POSTFIX = "postfix to be placed after each resulting network, for example ` via tun0`"
ARGHELP_IGNORE = "ignore non-valid input arguments (except the target network)"


def parse_arguments() -> Namespace:

    parser = ArgumentParser()
    parser.add_argument('network', type=str, help=ARGHELP_NETWORK)
    parser.add_argument(
        '-a', '--addresses', type=str, metavar='NETS',
        help=ARGHELP_ADDRESSES)

    parser.add_argument(
        '-s', '--separator', type=str, metavar='SEP',
        help=ARGHELP_SEPARATOR, default='\n')
    parser.add_argument(
        '-p', '--prefix', type=str, metavar='STR',
        help=ARGHELP_PREFIX,    default='')
    parser.add_argument(
        '-P', '--postfix', type=str, metavar='STR',
        help=ARGHELP_POSTFIX,   default='')

    parser.add_argument(
        '-i', '--ignore', action='store_true', help=ARGHELP_IGNORE)

    return parser.parse_args()


def die(code: int, message: Optional[str] = None) -> NoReturn:
    if message:
        if code != 0:
            out = sys.stderr
        else:
            out = sys.stdout
        print(message, file=out)
    sys.exit(code)


def is_string_a_valid_ip_address(item: str) -> bool:
    try:
        ip_address(item)
        return True
    except ValueError:
        return False


def is_string_a_valid_ip_network(item: str, strict: bool = False) -> bool:
    if not strict:
        try:
            ip_network(item)
            return True
        except ValueError:
            return False
    else:
        return bool(is_string_a_valid_ip_network(item) and not \
                    is_string_a_valid_ip_address(item))


def exclude_addresses(
        target_network:       Union[IPv4Network, IPv6Network],
        addresses_to_exclude: Union[List[IPv4Network], List[IPv6Network]]
) -> Union[Iterator[IPv4Network], Iterator[IPv6Network]]:

    addresses_to_exclude = sorted(collapse_addresses(addresses_to_exclude))

    # Process addresses.
    networks: Union[List[IPv4Network], List[IPv6Network]] = []
    for address in addresses_to_exclude:
        if address.subnet_of(target_network):
            networks.extend(target_network.address_exclude(address))
    networks = sorted(set(networks))

    # Post-process resulting network list.
    networks_to_remove = []
    for network in networks:
        for address in addresses_to_exclude:
            if address.subnet_of(network) or address.supernet_of(network):
                networks_to_remove.append(network)
    for network in networks_to_remove:
        if network in networks:
            networks.remove(network)

    return collapse_addresses(networks)


def validate_args(
        target_net: str, addrs_str: str
) -> Union[tuple[Union[IPv4Network, IPv6Network], str], NoReturn]:

    if not is_string_a_valid_ip_network(target_net):
        die(1, f"{target_net} is not a valid ip network.")
    elif not addrs_str:
        die(2, f"Missing addresses argument. It must be a {ARGHELP_ADDRESSES}.")

    target_net = ip_network(target_net)
    addrs_str = str(addrs_str).strip()

    return target_net, addrs_str


def process_args(
        target_net: Union[str, IPv4Network, IPv6Network],
        addrs_str: str
) -> Union[tuple[set, set, set, set], NoReturn]:

    addr_objs = set()
    inv_addrs = set()
    mis_addrs = set()
    irr_addrs = set()

    if is_string_a_valid_ip_network(addrs_str):
        net_a = ip_network(addrs_str)
        if not isinstance(net_a, type(target_net)):
            mis_addrs.add(net_a)
        elif not net_a.subnet_of(target_net):
            if net_a.supernet_of(target_net):
                irr_addrs.add(net_a)
            else:
                irr_addrs.add(net_a)
        else:
            addr_objs.add(net_a)
    else:
        if ',' in addrs_str:
            addr_list = addrs_str.split(',')
            addrs = set(a.strip() for a in addr_list if a.strip() != '')
        else:
            if ' ' not in addrs_str:
                die(2, f"{addrs_str} is not a valid ip network.")
            addr_list = addrs_str.split()
            addrs = set(a.strip() for a in addr_list if a.strip() != '')

        for a in addrs:
            if not is_string_a_valid_ip_network(a, strict=False):
                inv_addrs.add(a)
                continue

            net_a = ip_network(a)

            if not isinstance(net_a, type(target_net)):
                mis_addrs.add(net_a)
            elif not net_a.subnet_of(target_net):
                irr_addrs.add(a)
            else:
                addr_objs.add(net_a)

    return addr_objs, inv_addrs, mis_addrs, irr_addrs


def print_errors_and_exit(inv_addrs, mis_addrs, irr_addrs) -> NoReturn:

    wrong_stuff_message_list = []
    for wrong_stuff in zip(
            ('invalid address', 'misfitting address', 'irrelevant address'),
            (inv_addrs, mis_addrs, irr_addrs)):
        wrong_stuff_len = len(wrong_stuff[1])
        if wrong_stuff_len > 0:
            plural = 'es' if wrong_stuff_len > 1 else ''
            wrong_stuff_str = ' '.join(str(item) for item in wrong_stuff[1])
            wrong_stuff_message_list.append(
                f"{wrong_stuff[0] + plural + ': ' + wrong_stuff_str}"
            )

    die(2, '\n'.join(wrong_stuff_message_list).strip())


def print_result_and_exit(result_nets, separator, prefix, postfix) -> NoReturn:
    die(0, separator.join(
        (prefix+str(n)+postfix for n in result_nets)
    ).strip())


def main() -> NoReturn:

    args = parse_arguments()

    separator = args.separator
    prefix = args.prefix
    postfix = args.postfix

    target_net, addrs_str = validate_args(args.network, args.addresses)
    addr_objs, inv_addrs, mis_addrs, irr_addrs = process_args(target_net,
                                                              addrs_str)

    if not args.ignore and (inv_addrs or mis_addrs or irr_addrs):
        print_errors_and_exit(inv_addrs, mis_addrs, irr_addrs)
    else:
        result_nets = sorted(list(
            exclude_addresses(target_net, (a for a in addr_objs))
        ))
        if len(result_nets) == 0:
            die(0, target_net)
        print_result_and_exit(result_nets, separator, prefix, postfix)


if __name__ == '__main__':
    main()
