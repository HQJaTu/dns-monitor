import datetime
from .monitor import Monitor


class MonitorParentAuthoritativeCompareLocal(Monitor):
    """
    Find parent of authoritative DNS for given record.
    Monitor for its value to match local.
    Note: This is typically used for DNSSEC.
    """

    def __init__(self, dns, additional_dns=None):
        super(MonitorParentAuthoritativeCompareLocal, self).__init__(dns, additional_dns=additional_dns)

        self.initial_local_answers = None
        raise Exception("Not yet implemented!")