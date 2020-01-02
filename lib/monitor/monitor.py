import time
import signal


class Monitor:

    def __init__(self, dns, additional_dns=None):
        self.dns = dns
        self.additional_dns = additional_dns

    def init_monitor(self, host_to_query, rr_type_to_query, verbose=False):
        pass

    @staticmethod
    def exit_gracefully(signum, frame):
        """
        Signal handler.
        Stop main loop and quit.
        :param signum:
        :param frame:
        :return:
        """
        print("\nQuit.")
        exit(0)

    def get_authorities(self, host, verbose=False):
        authorities = self.dns.find_authoritative_nameservers(host, verbose=verbose)

        print("Found following authorities for %s:\n%s" % (
            host,
            '\n'.join("{!s} = {!s}".format(key, val) for (key, val) in authorities.items()))
              )
        if self.additional_dns:
            print("Also using following DNS: %s" % (
                ', '.join(val for val in self.additional_dns))
                  )

    def get_parents_of_authority(self, host_in, verbose=False):
        host = host_in.split('.')
        if len(host) < 2:
            raise Exception("get_parents_of_authority() will fail for host '%s'. Doesn't have a parent!" % host_in)

        host = '.'.join(host[1:])
        authorities = self.dns.find_authoritative_nameservers(host, verbose=verbose)

        print("Found following authorities for %s:\n%s" % (
            host,
            '\n'.join("{!s} = {!s}".format(key, val) for (key, val) in authorities.items()))
              )
        if self.additional_dns:
            print("Also using following DNS: %s" % (
                ', '.join(val for val in self.additional_dns))
                  )

    def local_query(self, host, rr_type):
        answers = self.dns.query(host, rr_type)

        for rdata in answers:
            if rr_type.upper() == 'A':
                answer = rdata.address
            elif rr_type.upper() == 'DNSKEY':
                answer = '%s %s' % (rdata.__class__.__name__, str(rdata))
            else:
                answer = '%s %s' % (rdata.__class__.__name__, str(rdata))
            print('Local server result for %s: %s' % (host, answer))

        return answers

    def compare_local_and_remote(self, local_answers, authority_answers, additional_answers, verbose=False):
        replies = []
        statuses = {}
        for authority, answer in authority_answers.items():
            if answer != local_answers:
                statuses[authority] = False
                replies.append("Authority %s not returning local result! returned: %s, expected %s" %
                               (authority, ', '.join(answer), ', '.join(local_answers))
                               )
            else:
                statuses[authority] = True
                if verbose:
                    print("Authority %s ok. returned: %s" % (authority, ', '.join(answer)))
        if self.dns.authorities and not authority_answers:
            replies.append("No authority answers received!")
        for additional_server, answer in additional_answers.items():
            if answer != local_answers:
                statuses[additional_server] = False
                statuses = False
                replies.append("Additional DNS %s fail! returned: %s" % (additional_server, ', '.join(answer)))
            else:
                statuses[additional_server] = True
                if verbose:
                    print("Additional DNS %s ok. returned: %s" % (additional_server, ', '.join(answer)))

        return statuses, replies

    def single_pass(self, *args, **kwargs):
        self.monitor(*args, **kwargs)
        print('')

    def continuous(self, host, rr_type, interval=0, only_fail=False, stop_on_success=True, **kwargs):
        # Keep looping
        signal.signal(signal.SIGINT, Monitor.exit_gracefully)
        signal.signal(signal.SIGTERM, Monitor.exit_gracefully)

        interval_to_use = int(interval)
        last_ok = 'never'
        while True:
            (stat, messages, last_ok, local_ttl) = self.monitor(host, rr_type, **kwargs)

            if stop_on_success and stat:
                print('')
                break

            time.sleep(interval_to_use)

#    def monitor(self):
#        raise Exception("Internal: Not implemented in base class!")
