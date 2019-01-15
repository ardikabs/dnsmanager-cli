import dns.update
import dns.tsigkeyring
import dns.resolver
import dns.rdatatype
import dns.query
import dns.zone
import dns.rdataclass
from dns.exception import DNSException
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class RecordTypeEnum(Enum):
    A = dns.rdatatype.A
    CNAME = dns.rdatatype.CNAME
    PTR = dns.rdatatype.PTR
    MX = dns.rdatatype.MX
    TXT = dns.rdatatype.TXT
    SRV = dns.rdatatype.SRV

class DNSService(object):

    def __init__(self, nameserver, keyring_name, keyring_value, timeout=0):
        self.nameserver = nameserver
        self.keyring = dns.tsigkeyring.from_text({
            keyring_name: keyring_value
        })
        self.timeout = timeout if timeout else 10
    
    def _set_record_attribute(self, **kwargs):
        expected_attribute = ("zone", "record_type", "record_name", "record_content", "record_ttl")
        for attr in expected_attribute:
            if kwargs.get(attr):
                if attr == "record_type":
                    rtype = kwargs.get(attr, "").upper()
                    setattr(self, attr, RecordTypeEnum[rtype])
                else:
                    setattr(self, attr, kwargs.get(attr))


    def add_record(self, **kwargs):
        self._set_record_attribute(**kwargs)

        data = dns.update.Update(self.zone, keyring=self.keyring)
        data.add(self.record_name, self.record_ttl, self.record_type.value, self.record_content)
        result = dns.query.tcp(data, self.nameserver, timeout=self.timeout)
        return self.response(result)
    
    def replace_record(self, **kwargs):
        self._set_record_attribute(**kwargs)

        data = dns.update.Update(self.zone, keyring=self.keyring)
        data.replace(self.record_name, self.record_ttl, self.record_type.value, self.record_content)
        result = dns.query.tcp(data, self.nameserver, timeout=self.timeout)
        return self.response(result)

    def remove_record(self, **kwargs):
        self._set_record_attribute(**kwargs)

        data = dns.update.Update(self.zone, keyring=self.keyring)
        data.delete(self.record_name)
        result = dns.query.tcp(data, self.nameserver, timeout=self.timeout)
        return self.response(result)

    def response(self, result):
        return str(result).split("\n")[2].split(" ")[1]

    def import_records(self, domain):
        zone = None
        answer = dns.resolver.query(domain, "NS")
        for rdata in answer:
            try:
                ns = str(rdata)
                zone = dns.zone.from_xfr(dns.query.xfr(ns, domain))
            except DNSException as e:
                logger.error(str(e))
        
        records = []
        if zone:        
            for name, node in zone.nodes.items():
                todict = {}
                for rdataset in node.rdatasets:
                    for rdata in rdataset:
                        if rdataset.rdtype in (
                                dns.rdatatype.A, 
                                dns.rdatatype.CNAME, 
                                dns.rdatatype.MX,
                            ):
                            todict["zone"] = domain  
                            todict["name"] = f"{name}"
                            todict["content"] = rdata.to_text()                
                            todict["rtype"] = dns.rdatatype.to_text(rdataset.rdtype)
                            todict["ttl"] = rdataset.ttl                            
                            todict["representation"] = str(rdataset)
                if todict:
                    records.append(todict)
        return records

