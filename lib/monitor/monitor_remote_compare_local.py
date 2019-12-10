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

        # Get local opinion
        local_answers, local_ttl = self.dns.run_local_query(host, rr_type, verbose)

        # Get remote opinion
        authority_answers, additional_answers, replies = self.dns.run_query(host, rr_type,
                                                                            self.additional_dns,
                                                                            timeout,
                                                                            verbose=verbose)
        # Compare local to remote
        statuses, messages = self.compare_local_and_remote(local_answers,
                                                           authority_answers, additional_answers,
                                                           verbose=verbose)

        # Interpret the results
        servers_queried = len(authority_answers) + len(additional_answers)
        successes = len(list(filter(lambda x: x == True, statuses.values())))
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        success = successes == servers_queried

        if success:
            last_ok = now
            output = "%s - queries ok. Local DNS TTL %d seconds" % (now, local_ttl)
        else:
            output = "%s - Fail! %d out of %d ok. Local DNS TTL %d seconds. Last ok: %s" % \
                     (now, successes, servers_queried, local_ttl, last_ok)

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

        return success, messages, last_ok, None
