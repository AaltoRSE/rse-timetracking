import json

class Project():
    def __init__(self):
        self.iid = None
        self.state = None
        self.title = None
        self.timeestimate = None
        self.timespent = None
        self.timespent_list = [ ]
        self.assignee = None
        self.time_created = None
        self.time_updated = None
        self.unit_list = [ ]
        self.funding_list = [ ]
        self.status_list = [ ]
        self.task_list = [ ]
        self.label_list = [ ]   # labels not detected as the above
        self.timespent = 0
        self.time_spent_list = [ ]
        self.kpi_list = [ ]
        self.metadata_list = [ ]

    @property
    def unit(self):     return '+'.join(self.unit_list)
    @property
    def funding(self):  return '+'.join(self.funding_list)
    @property
    def status(self):   return '+'.join(self.status_list)

    def __getstate__(self):
        return self.__dict__
    def __setstate__(self, state):
        self.__dict__ = state

    @classmethod
    def dumps(self, objs):
        """List of objects → serialized string"""
        data = [ obj.__getstate__() for obj in objs ]
        return json.dumps(data, indent=2)
    def loads(self, data):
        data = json.loads(data)
        objs = [ ]
        for d in data:
            p = Project()
            p.__setstate__(d)
            objs.append(p)
        return objs
