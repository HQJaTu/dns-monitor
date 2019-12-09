import sys
import datetime
from .monitor import Monitor


class MonitorLocalExpected(Monitor):

    def __init__(self, dns, expected):
        super(MonitorLocalExpected, self).__init__(dns)

        self.expected = expected
        self.additional_dns = None
        #print("Resolver: %s" % dns.default_resolver.nameservers)

    def compare(self, local_answers, verbose=False):
        replies = []
        stat = True
        for answer in local_answers:
            if answer != self.expected:
                stat = False
                replies.append("Local not returning expected result! returned: %s, expected %s" %
                               (', '.join(answer), ', '.join(self.expected))
                               )
            elif verbose:
                print("Local ok. returned: %s" % answer)
        if not local_answers:
            replies.append("No local answers received!")
            stat = False

        return stat, replies

    def monitor(self, host, rr_type, expected,
                timeout=None,
                only_fail=False, stop_on_success=True, last_ok=None, verbose=False):
        answers, local_ttl = self.dns.run_local_query(host, rr_type,
                                                       verbose=verbose)
        stat, messages = self.compare(answers, verbose=verbose)
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
                print("%s - queries ok. Local DNS TTL %d seconds      " %
                      (now, local_ttl), end="\r", flush=True)
            else:
                print("\n%s - Fail! Last ok: %s" % (now, last_ok), end="\r", flush=True)
                if messages:
                    print("\n".join(messages), end='')

        return stat, messages, last_ok, local_ttl
