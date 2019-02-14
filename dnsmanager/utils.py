
class JSONParser:

    def __init__(self, name, dict_={}):
        self._name = name
        self._keys = list()
        for attr in dict_:
            if isinstance(dict_.get(attr), dict):
                dict_[attr] = self.__class__.from_dict(attr, dict_.get(attr, None))
            elif isinstance(dict_.get(attr), list):
                dict_[attr] = list(self.__class__(attr, dt) for dt in dict_.get(attr))
            self._keys.append(attr)
        self.__dict__.update(dict_)

    def __repr__(self):
        items = (f"{k}={self.__dict__.get(k) !r}" for k in self._keys)
        return f"{self._name}({', '.join(items)})"
    
    def __str__(self):
        items = (f"{k}={self.__dict__.get(k) !s}" for k in self._keys)
        return f"{self._name}({', '.join(items)})"
    
    def to_dict(self):
        todict = {}
        for key in self.__dict__:
            if key in self._keys:
                if isinstance(self.__dict__[key], JSONParser):
                    todict[key] = self.__dict__[key].to_dict()
                else:
                    todict[key] = self.__dict__[key]
        return todict

    def export(self, name=None):
        """  
            >>>
            json_response = {
                "success": True,
                "data": {
                    "uid": "2110141010",
                    "full_name": "Ardika Bagus Saputro",
                    "first_name": "Ardika",
                    "middle_name": "Bagus",
                    "last_name": "Saputro",
                    "hobbies": ["Read", "Hiking", "Code"],
                    "skills": [
                        "Python", "Golang", "Distributed System", 
                        "Infrastructure Best Practice", "DevOps Related", 
                        "Linux", "Monitoring", "Containerization"
                    ],
                    "tools":["Docker", "Consul", "Ansible", "Packer", "Terraform"],
                    "role": "Infrastructure with Code guy",
                    "title": "Site Infrastructure Engineer"
                }
            }
            obj = JSONParser("ObjResponse", json_response)
            data_obj = obj.data.export("DataObj")
            return:
                DataObj(uid='2110141010', full_name='Ardika Bagus Saputro', first_name='Ardika', ...)
        """
        if isinstance(self, JSONParser):
            if name:
                self._name = name
            return self 
        else:
            raise ValueError("Field is not a dict type, so it can't convert to object")

    @classmethod
    def from_dict(cls, name, dict_={}):
        if dict_ is None:
            return None

        doc = cls(name, dict_)
        return doc
        
def build_dict(seq, keys):
    if isinstance(keys, tuple):
        keysgroups = []
        for index, d in enumerate(seq):
            temp = [] 
            for key in keys:
                temp.append(d[key])
            keysgroups.append(".".join(temp))

        return dict((d[1], dict(d[0], index=index)) for (index, d) in enumerate(zip(seq, keysgroups)))

    else:
        return dict((d[keys], dict(d, index=index)) for (index, d) in enumerate(seq))