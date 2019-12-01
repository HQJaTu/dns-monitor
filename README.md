# DNS monitor
Utility to monitor DNS changes and propagation.

## Use cases
In all scenarios you need to know a RR in DNS to monitor changes for.
Typical RR would be A-record to indicate IPv4-address.

There exist two modes of operation:
* Single pass: Check if change is done, report status and quit
* Looping with interval: Loop and monitor a change. By default stop looping with success is measured.

### Wait for propagation
Local DNS has different value than authoritative DNS.
Keep looping until both DNS have same value.

Assumption here is the authoritative DNS to have the new value
and your local DNS to have the old value. In DNS there is always propagation delay.

### Wait for expected change to take place in authoritative DNS
You're expecting a future change and want to know when/if it has taken place.

Assumption here is to wait for a known change which hasn't yet been made available at authoritative DNS.
Typically this is needed when you cannot make the change yourself and need to wait for somebody else to act on the change.

When authoritative DNS has the record, a handy trick is to switch modes and run this tool in _Wait for propagation_ -mode.

### Wait for expected RR to appear in DNS
A variation of previous one. In this scenario the RR doesn't yet exist in authoritative DNS.

## Usage:
