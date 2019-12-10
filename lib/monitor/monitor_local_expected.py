import sys
import datetime
from .monitor import Monitor


class MonitorLocalExpected(Monitor):

    def __init__(self, dns, expected):
        super(MonitorLocalExpected, self).__init__(dns, additional_dns=None)

        self.expected = expected
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

    def monitor(self, host, rr_type,
                timeout=None,
                only_fail=False, stop_on_success=True, last_ok=None, verbose=False):
        answers, local_ttl = self.dns.run_local_query(host, rr_type,
                                                       verbose=verbose)
        success, messages = self.compare(answers, verbose=verbose)
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        if success:
            last_ok = now
            output = "%s - queries ok. Local DNS TTL %d seconds" % (now, local_ttl)
        else:
            output = "%s - Fail! Local DNS TTL %d seconds. Last ok: %s" % \
                     (now, local_ttl, last_ok)

        if success:
            if not only_fail or stop_on_success:
                print(output, end="\r", flush=True)
        else:
            if only_fail:
                print("\n%s", output, flush=True)
                if verbose:
                    print("\n".join(messages), end='')
            else:
                print(output, flush=True)

        return success, messages, last_ok, local_ttl