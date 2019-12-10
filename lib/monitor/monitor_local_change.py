import sys
import datetime
from .monitor_local_expected import MonitorLocalExpected


class MonitorLocalChange(MonitorLocalExpected):

    def __init__(self, dns, host, rr_type):
        super(MonitorLocalChange, self).__init__(dns, None)
        self.query_host = host
        self.query_rr_type = rr_type
        initial_result = self.local_query(host, rr_type)
        # self.expected = list(map(lambda x: str(x), initial_result))
        self.expected = str(initial_result[0])

    def monitor(self, host, rr_type,
                timeout=None,
                only_fail=False, stop_on_success=True, last_ok=None, verbose=False):
        # Don't bring anything own here.
        # Just call the parent's method with alternate host and RR-type
        success, messages, last_ok, local_ttl = super(MonitorLocalChange, self).monitor(self.query_host,
                                                                                        self.query_rr_type,
                                                                                        timeout=timeout,
                                                                                        only_fail=only_fail,
                                                                                        stop_on_success=stop_on_success,
                                                                                        last_ok=last_ok,
                                                                                        verbose=verbose)

        # This is our twist: If value matches the expected, that's a fail!
        # We wait the value to CHANGE from initial.
        success = not success

        return success, messages, last_ok, local_ttl