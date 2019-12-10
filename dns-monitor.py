#!/usr/bin/env python3

# vim: autoindent tabstop=4 shiftwidth=4 expandtab softtabstop=4 filetype=python

import sys
import argparse
from lib.dns import *
from lib.monitor import *

DEFAULT_DNS_TIMEOUT = 5.0


def main():
    parser = argparse.ArgumentParser(description='DNS query helper tool')
    parser.add_argument('host',
                        help='FQDN to query')
    parser.add_argument('-t', '--rr-type', dest='rr_type', default='A',
                        help='DNS RR-type to query. Default = A')
    parser.add_argument('--override-local-dns', dest='local_dns', action='append',
                        help='Use this DNS/DNSes as local instead of default one/ones')
    parser.add_argument('-d', '--dns', dest='additional_dns', action='append',
                        help='Additional DNS-servers to use')
    parser.add_argument('-i', '--interval', dest='interval',
                        help='Keep looping forever with given interval')
    parser.add_argument('--continue-on-success', dest='interval_stop_on_success', action='store_false', default=True,
                        help='Keep looping with given --interval even if a success is found')
    parser.add_argument('--print-only-fail', action='store_true', dest='only_fail',
                        help="Default is to print all results. Keep output terse.")
    parser.add_argument('-W', '--timeout', dest='timeout', default=DEFAULT_DNS_TIMEOUT,
                        help='Time to wait fo DNS response. %s [seconds]' % DEFAULT_DNS_TIMEOUT)
    parser.add_argument('--mode-match-authoritative-to-local', dest='mode_remote_compare_to_local',
                        action='store_true',
                        help='Mode: Monitor both local and authoritative DNS. Wait for their values to match.')
    parser.add_argument('--mode-monitor-local-expected', dest='mode_local_expected', metavar='EXPECTED_VALUE',
                        help='Monitor for an upcoming change. Wait for expected result to appear in local DNS.')
    parser.add_argument('--mode-monitor-remote-expected', dest='mode_remote_expected', metavar='EXPECTED_VALUE',
                        help='Monitor for an upcoming change. Wait for expected result to appear in authoritative DNS.')
    parser.add_argument('--mode-monitor-local-change', dest='mode_local_change', action='store_true',
                        help='Monitor for an upcoming change. Wait for local DNS value to change.')
    parser.add_argument('--mode-monitor-remote-change', dest='mode_remote_change', action='store_true',
                        help='Monitor for an upcoming change. Wait for authoritative DNS value to change.')
    parser.add_argument('--verbose', '-v', action='store_true', default=False,
                        help="Noisy. Output status.")

    args = parser.parse_args()

    if not args.host:
        parser.print_help(sys.stderr)
        exit(1)

    dns = DNS(default_resolver=args.local_dns, query_timeout=args.timeout)
    monitor = None
    if args.mode_remote_compare_to_local:
        monitor = MonitorRemoteCompareLocal(dns, additional_dns=args.additional_dns)
    elif args.mode_local_expected:
        monitor = MonitorLocalExpected(dns, args.mode_local_expected)
    elif args.mode_remote_expected:
        monitor = MonitorRemoteExpected(dns, additional_dns=args.additional_dns)
    elif args.mode_local_change:
        monitor = MonitorLocalChange(dns, args.host, args.rr_type)
    elif args.mode_remote_change:
        raise Exception("Not yet --mode-monitor-remote-change !")
    else:
        print("Need --mode-* to operate. Cannot continue.", file=sys.stderr)
        exit(1)

    monitor.init_monitor(args.host, args.rr_type)

    # Do a single pass only?
    args.timeout = int(args.timeout)
    if not args.interval:
        if args.mode_remote_compare_to_local:
            monitor.single_pass(args.host, args.rr_type,
                                timeout=args.timeout, verbose=args.verbose)
        elif args.mode_local_compare_to_remote:
            raise Exception("Not yet --mode-monitor-local-to-match-remote !")
        elif args.mode_local_expected:
            monitor.single_pass(args.host, args.rr_type,
                                timeout=args.timeout, verbose=args.verbose)
        elif args.mode_remote_expected:
            monitor.single_pass(args.host, args.rr_type,
                                timeout=args.timeout, verbose=args.verbose)
        elif args.mode_local_change:
            monitor.single_pass(None, None,
                                timeout=args.timeout, verbose=args.verbose)
        elif args.mode_remote_change:
            raise Exception("Not yet --mode-monitor-remote-change !")
        else:
            raise Exception("Internal: Oh really?")
        exit(0)

    if args.mode_remote_compare_to_local:
        monitor.continuous(args.host, args.rr_type,
                           interval=args.interval, only_fail=args.only_fail,
                           stop_on_success=args.interval_stop_on_success,
                           timeout=args.timeout, verbose=args.verbose)
    elif args.mode_local_expected:
        monitor.continuous(args.host, args.rr_type,
                           interval=args.interval, only_fail=args.only_fail,
                           stop_on_success=args.interval_stop_on_success,
                           timeout=args.timeout, verbose=args.verbose)
    elif args.mode_remote_expected:
        monitor.continuous(args.host, args.rr_type,
                           interval=args.interval, only_fail=args.only_fail,
                           stop_on_success=args.interval_stop_on_success,
                           timeout=args.timeout, verbose=args.verbose)
    elif args.mode_local_change:
        monitor.continuous(None, None,
                           interval=args.interval, only_fail=args.only_fail,
                           stop_on_success=args.interval_stop_on_success,
                           timeout=args.timeout, verbose=args.verbose)
    elif args.mode_remote_change:
        raise Exception("Not yet --mode-monitor-remote-change !")
    else:
        raise Exception("Internal: Oh really?")


if __name__ == "__main__":
    main()
