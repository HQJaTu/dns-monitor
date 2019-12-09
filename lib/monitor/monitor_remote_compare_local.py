import datetime
from .monitor import Monitor


class MonitorRemoteCompareLocal(Monitor):

    def __init__(self, dns, additional_dns=None):
        super(MonitorRemoteCompareLocal, self).__init__(dns, additional_dns=additional_dns)

        self.initial_local_answers = None

    def init_monitor(self, host_to_query, rr_type_to_query, verbose=False):
        # Do local first
        self.initial_local_answers, local_ttl = self.dns.run_local_query(host_to_query, rr_type_to_query,
                                                                         verbose=verbose)
        print("Comparing against your local nameserver: %s" % self.dns.default_ns)

        self.get_authorities(host_to_query, verbose=verbose)

    def monitor(self, host, rr_type, timeout=None,
                only_fail=False, stop_on_success=True, last_ok=None, verbose=False):
        local_answers, local_ttl = self.dns.run_local_query(host, rr_type, verbose)
        authority_answers, additional_answers, replies = self.dns.run_query(host, rr_type,
                                                                            self.additional_dns,
                                                                            timeout,
                                                                            verbose=verbose)
        stat, messages = self.compare_local_and_remote(local_answers, authority_answers, additional_answers,
                                                       verbose=verbose)
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if only_fail:
            if stat:
                last_ok = now
                if stop_on_success:
                    print("%s - queries ok. Local DNS TTL %d seconds      " % (now, local_ttl), end="\r",
                          flush=True)
            else:
                print("%s - Fail! Last ok: %s" % (now, last_ok), flush=True)
        else:
            if stat:
                last_ok = now
                print("%s - queries ok. Local DNS TTL %d seconds      " % (now, local_ttl), end="\r",
                      flush=True)
            else:
                print("\n%s - Fail! Last ok: %s" % (now, last_ok), flush=True)
                print("\n".join(messages), end='')

        return stat, messages, last_ok, None
