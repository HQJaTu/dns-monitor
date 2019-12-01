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
    parser.add_argument('--continue-on-success', dest='interval_stop_on_success', action='store_true', default=True,
                        help='Keep looping with given --interval even if a success is found')
    parser.add_argument('--print-only-fail', action='store_true', dest='only_fail',
                        help="Default is to print all results. Keep output terse.")
    parser.add_argument('-W', '--timeout', dest='timeout', default=DEFAULT_DNS_TIMEOUT,
                        help='Time to wait fo DNS response. %s [seconds]' % DEFAULT_DNS_TIMEOUT)
    parser.add_argument('--expected', metavar='EXPECTED_VALUE',
                        help='Ignore local DNS. Monitor for an upcoming change. Wait for expected result to appear.')
    parser.add_argument('--verbose', '-v', action='store_true', default=False,
                        help="Noisy. Output status.")

    args = parser.parse_args()

    if not args.host:
        parser.print_help(sys.stderr)
        exit(1)

    dns = DNS(default_resolver=args.local_dns, query_timeout=args.timeout)
    monitor = Monitor(dns)
    answers = dns.query(args.host, args.rr_type)

    for rdata in answers:
        if args.rr_type.upper() == 'A':
            answer = rdata.address
        elif args.rr_type.upper() == 'DNSKEY':
            answer = '%s %s' % (rdata.__class__.__name__, str(rdata))
        else:
            answer = '%s %s' % (rdata.__class__.__name__, str(rdata))
        print('Local server result for %s: %s' % (args.host, answer))

    authorities = dns.find_authoritative_nameservers(args.host, verbose=args.verbose)

    print("Found following authorities for %s:\n%s" % (
        args.host,
        '\n'.join("{!s} = {!s}".format(key, val) for (key, val) in authorities.items()))
          )
    if args.additional_dns:
        print("Also using following DNS: %s" % (
            ', '.join(val for val in args.additional_dns))
              )
    print("Comparing against your local nameserver: %s" % dns.default_ns)

    # Do a single pass only?
    args.timeout = int(args.timeout)
    if not args.interval:
        monitor.single_pass(args.host, additional_dns=args.additional_dns, timeout=args.timeout,
                            expected=args.expected, verbose=args.verbose)
        exit(0)

    monitor.continuous(args.host, interval=args.interval, only_fail=args.only_fail,
                       stop_on_success=args.interval_stop_on_success,
                       additional_dns=args.additional_dns, timeout=args.timeout,
                       expected=args.expected, verbose=args.verbose)


if __name__ == "__main__":
    main()
