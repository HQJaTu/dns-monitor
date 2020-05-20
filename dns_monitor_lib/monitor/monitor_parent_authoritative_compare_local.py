import datetime
from .monitor_authoritative_compare_local import MonitorAuthoritativeCompareLocal


class MonitorParentAuthoritativeCompareLocal(MonitorAuthoritativeCompareLocal):
    """
    Find parent of authoritative DNS for given record.
    Monitor for its value to match local.
    Note: This is typically used for DNSSEC.
    """

    def __init__(self, dns, additional_dns=None):
        super(MonitorParentAuthoritativeCompareLocal, self).__init__(dns, additional_dns=additional_dns)

        self.initial_local_answers = None

    def init_monitor(self, host_to_query, rr_type_to_query, verbose=False):
        # Do local first
        self.initial_local_answers, local_ttl = self.dns.run_local_query(host_to_query, rr_type_to_query,
                                                                         verbose=verbose)
        print("Comparing against your local nameserver: %s" % self.dns.default_ns)

        self.get_parents_of_authority(host_to_query, verbose=verbose)
