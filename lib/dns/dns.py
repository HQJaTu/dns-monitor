import dns.resolver  # from pip dnspython3


class DNS:
    DEFAULT_DNS_TIMEOUT = 5.0

    def __init__(self, default_resolver=None, query_timeout=DEFAULT_DNS_TIMEOUT):

        # See what we want to use as default resolver
        if default_resolver:
            self.default_resolver = dns.resolver.Resolver()
            self.default_resolver.nameservers = default_resolver
        else:
            # Just use what dnspython3 detects
            self.default_resolver = dns.resolver.get_default_resolver()

        self.query_timeout = query_timeout
        self.default_resolver.lifetime = query_timeout
        self.default_ns = self.default_resolver.nameservers[0]
        self.authorities = {}

    def query(self, host, rr_type):
        try:
            answers = self.default_resolver.query(host, rr_type)
        except dns.resolver.NXDOMAIN:
            print(
                "Couldn't resolve %s-record for %s using %s. No such thing found!" % (rr_type, host, self.default_ns))
            exit(2)
        except dns.exception.Timeout:
            print("Couldn't resolve %s-record for %s using %s. Timed out!" % (rr_type, host, self.default_ns))
            exit(2)
        except dns.resolver.NoAnswer:
            print("Couldn't resolve %s-record for %s using %s. No answer!" % (rr_type, host, self.default_ns))
            exit(2)

        return answers

    def find_authoritative_nameservers(self, host, verbose=False):
        self.authorities = {}
        dns_query = dns.message.make_query(host, dns.rdatatype.A)
        resp = dns.query.udp(dns_query, self.default_ns, timeout=self.query_timeout)
        if resp.authority:
            auths = resp.authority[0]
        else:
            resp = self._get_authoritative_nameserver(dns_query, self.default_resolver, verbose=verbose)
            auths = resp.items
        if auths:
            for authority_rr in auths:
                if authority_rr.rdtype == dns.rdatatype.SOA:
                    authority = str(authority_rr.mname)
                elif authority_rr.rdtype == dns.rdatatype.NS:
                    authority = str(authority_rr.target)
                else:
                    raise Exception('Authority record type %s not implemented!' % authority_rr.__class__.__name__)

                try:
                    answers = self.default_resolver.query(authority, 'A')
                except dns.resolver.NXDOMAIN:
                    # Skip this
                    continue

                if answers:
                    self.authorities[authority] = answers[0].address
        if len(self.authorities) == 0:
            print("Couldn't find any authorities for %s" % host)
            exit(2)

        return self.authorities

    def _get_authoritative_nameserver(self, query_rr_in, resolver, verbose=False):
        depth = len(query_rr_in.question[0].name)
        nameserver = resolver.nameservers[0]
        # dns_query = dns.message.make_query(args.host, dns.rdatatype.A)
        query_rr = query_rr_in

        last = False
        while not last:
            query = query_rr.question[0].name
            s = query.split(depth)

            last = s[0].to_unicode() == u'@'
            sub = s[1]

            if verbose:
                print('get_authoritative_nameserver() Looking up %s on %s' % (sub, nameserver))
            query_rr = dns.message.make_query(sub, dns.rdatatype.NS)
            response = dns.query.udp(query_rr, nameserver)

            rcode = response.rcode()
            if rcode != dns.rcode.NOERROR:
                if rcode == dns.rcode.NXDOMAIN:
                    raise Exception('%s does not exist.' % sub)
                else:
                    raise Exception('Error %s' % dns.rcode.to_text(rcode))

            rrset = None
            if len(response.authority) > 0:
                rrset = response.authority[0]
            else:
                rrset = response.answer[0]

            rr = rrset[0]
            if rr.rdtype == dns.rdatatype.SOA:
                if verbose:
                    print('get_authoritative_nameserver() Same server is authoritative for %s' % sub)
            else:
                authority = rr.target
                if verbose:
                    print('get_authoritative_nameserver() %s is authoritative for %s' % (authority, sub))
                nameserver = resolver.query(authority).rrset[0].to_text()

            depth += 1

        return rrset

    def _make_query(self, host_to_query, rr_type_to_query):
        # Dynamically whip up a class from given string
        rr_type = dns.rdatatype.from_text(rr_type_to_query)
        if not rr_type:
            raise Exception("Cannot query for unknown RR-type '%s'" % rr_type_to_query)
        query_request = dns.message.make_query(host_to_query, rr_type)

        return query_request

    def run_local_query(self, host_to_query, rr_type_to_query, verbose=False):
        query_request = self._make_query(host_to_query, rr_type_to_query)
        replies = []
        local_answers = []
        local_ttl = None

        try:
            resp = dns.query.udp(query_request, self.default_ns)
        except dns.exception.Timeout:
            replies.append("Timed out on local server: %s" % self.default_ns)
            return False, None, replies
        for rr in resp.answer:
            if not local_ttl or rr.ttl < local_ttl:
                local_ttl = rr.ttl
            answer_str = str(rr.items[0])
            local_answers.append(answer_str)
        sorted(local_answers)
        if verbose:
            print("DEBUG: Local answers: %s" % local_answers)

        return local_answers, local_ttl

    def run_query(self, host_to_query, rr_type_to_query,
                  additional_servers, wait_seconds, verbose=False):
        """
        :param host_to_query: hostname to query DNS for
        :param rr_type_to_query: DNS RR-type to query for
        :param additional_servers:
        :param wait_seconds:
        :param expected:
        :param verbose:
        :return: bool, True if all servers match local or expected
        """
        if additional_servers:
            if not isinstance(additional_servers, list):
                additional_servers = [additional_servers]
        else:
            additional_servers = []

        authority_answers = {}
        additional_answers = {}
        replies = []
        query_request = self._make_query(host_to_query, rr_type_to_query)

        # Do authorities, if any
        for authority in self.authorities:
            authority_ip = self.authorities[authority]
            if verbose:
                print("DEBUG: Querying authority %s (%s) for %s" % (authority, authority_ip, query_request.question[0]))
            try:
                resp = dns.query.udp(query_request, authority_ip, timeout=wait_seconds)
            except dns.exception.Timeout:
                replies.append("Timed out on authority %s query" % authority)
                continue
            for answer in resp.answer:
                for rr in resp.answer:
                    if authority not in authority_answers:
                        authority_answers[authority] = []
                    answer_str = str(rr.items[0])
                    authority_answers[authority].append(answer_str)

                if authority in authority_answers:
                    sorted(authority_answers[authority])

        # Do additional servers, if any
        for additional_server in additional_servers:
            if verbose:
                print("Querying additional DNS: %s" % additional_server)
            try:
                resp = dns.query.udp(query_request, additional_server, timeout=wait_seconds)
            except dns.exception.Timeout:
                replies.append("Timed out on additional DNS %s query" % additional_server)
                continue
            for answer in resp.answer:
                for rr in resp.answer:
                    if additional_server not in additional_answers:
                        additional_answers[additional_server] = []
                    additional_answers[additional_server].append(rr.items[0].address)

                if additional_server in additional_answers:
                    sorted(additional_answers[additional_server])

        if additional_servers and not additional_answers:
            replies.append("No additional DNS answers received!")

        return authority_answers, additional_answers, replies
