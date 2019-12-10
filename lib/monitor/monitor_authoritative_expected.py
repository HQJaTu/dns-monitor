import datetime
from .monitor import Monitor


class MonitorAuthoritativeExpected(Monitor):

    def __init__(self, dns, additional_dns=None):
        super(MonitorAuthoritativeExpected, self).__init__(dns, additional_dns=additional_dns)
        pass

    def init_monitor(self, host_to_query, rr_type_to_query, verbose=False):
        self.get_authorities(host_to_query, verbose=verbose)

    def compare(self, expected, authority_answers, additional_answers, verbose=False):
        replies = []
        stat = True
        for authority, answer in authority_answers.items():
            if answer != expected:
                stat = False
                replies.append("Authority %s not returning expected result! returned: %s, expected %s" %
                               (authority, ', '.join(answer), ', '.join(expected))
                               )
            elif verbose:
                print("Authority %s ok. returned: %s" % (authority, ', '.join(answer)))
        if self.dns.authorities and not authority_answers:
            replies.append("No authority answers received!")
            stat = False
        for additional_server, answer in additional_answers.items():
            if answer != expected:
                stat = False
                replies.append("Additional DNS %s fail! returned: %s" % (additional_server, ', '.join(answer)))
            elif verbose:
                print("Additional DNS %s ok. returned: %s" % (additional_server, ', '.join(answer)))

        return stat, replies

    def monitor(self, host, rr_type, expected=None,
                timeout=None,
                only_fail=False, stop_on_success=True, last_ok=None, verbose=False):
        if not isinstance(expected, list):
            expected = [expected]

        authority_answers, additional_answers, replies = self.dns.run_query(host, rr_type,
                                                                            self.additional_dns,
                                                                            timeout,
                                                                            verbose=verbose)
        stat, messages = self.compare(expected, authority_answers, additional_answers,
                                      verbose=verbose)
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if only_fail:
            if stat:
                last_ok = now
                if stop_on_success:
                    print("%s - queries ok.                               " % now, end="\r", flush=True)
            else:
                print("%s - Fail! Last ok: %s" % (now, last_ok), flush=True)
        else:
            if stat:
                print("%s - queries ok.                                                 " %
                      (now), end="\r", flush=True)
            else:
                print("\n%s - Fail! Last ok: %s" % (now, last_ok), flush=True)
                print("\n".join(messages), end='')

        return stat, messages, last_ok, None
