import os

from deployerlib.log import Log
from deployerlib.exceptions import DeployerException


class Tasklist(object):
    """Manage the building of a tasklist"""

    def __init__(self, name='Deployment'):
        self.log = Log(self.__class__.__name__)
        self.name = name
        self._stages = {}
        self._stage_order = []
        self._pre_order = []
        self._post_order = []

    def create_stage(self, stage_name, pre=False, post=False, **settings):
        """Create a new stage"""

        if stage_name in self._stages:
            self.log.hidebug('Stage {0} already exists'.format(stage_name))
            return False

        self._stage_order.append(stage_name)

        if pre:
            self._pre_order.append(stage_name)
        elif post:
            self._post_order.append(stage_name)

        self._stages[stage_name] = {
          'name': stage_name,
          'hosts': [],
          'concurrency': 1,
          'concurrency_per_host': 1,
          'tasks': [],
        }

        if settings:
            self.set(stage_name, **settings)

        return True

    def get(self, stage_name, setting):
        """Get a setting from the specified queue"""

        self._exists_or_die(stage_name)

        return self._stages[stage_name].get(setting)

    def set(self, stage_name, **settings):
        """Apply settings (such as concurrency) to a stage"""

        self._exists_or_die(stage_name)
        self._stages[stage_name].update(settings)

        return True

    def unset(self, stage_name, setting_name):
        """Remove a setting from a stage
           Does nothing if the setting does not exist
           Returns the value of the setting that has been removed (returns None if the setting did not exist)
        """

        self._exists_or_die(stage_name)

        return self._stages[stage_name].pop(setting_name, None)

    def add_hosts(self, stage_name, hostlist):
        """Add to the list of hosts affected by this stage"""

        if type(hostlist) is not list:
            hostlist = [hostlist]

        added_hosts = []

        for host in hostlist:
            if not host in self._stages[stage_name]['hosts']:
                self._stages[stage_name]['hosts'].append(host)
                added_hosts.append(host)

        self._stages[stage_name]['hosts'].sort()

        return added_hosts

    def stages(self):
        """Return a list of queue names"""

        return self._stages.keys()

    def get_position(self, stage_name):
        """Get the position of a stage"""

        self._exists_or_die(stage_name)

        return self._stage_order.index(stage_name)

    def set_position(self, stage_name, pos):
        """Move a stage to a different position"""

        self._exists_or_die(stage_name)

        cur_pos = self.get_position(stage_name)

        return self._stage_order.insert(pos, self._stage_order.pop(cur_pos))

    def add(self, stage_name, task):
        """Add a task to the stage named stage_name"""

        self._exists_or_die(stage_name)

        if task in self._stages[stage_name]['tasks']:
            self.log.hidebug('Stage {0} discarding duplicate task: {1}'.format(stage_name, task))
            return False

        self.log.hidebug('Adding task to stage: "{0}"'.format(stage_name))
        self._stages[stage_name]['tasks'].append(task)

        return True

    def remove(self, stage_name, tasks):
        """Remove a task from a queue and return the tasks that have been removed"""

        self._exists_or_die(stage_name)

        remove_tasks = [x for x in self._stages[stage_name]['tasks'] if x in tasks]
        self.log.hidebug('Removing tasks {0} from {1}'.format(len(remove_tasks), stage_name))
        self._stages[stage_name]['tasks'] = [x for x in self._stages[stage_name]['tasks'] if not x in remove_tasks]

        return remove_tasks

    def tasks(self, stage_name):
        """Return the list of all tasks in the queue"""

        self._exists_or_die(stage_name)

        return self._stages[stage_name]['tasks']

    def is_empty(self):
        """Return True if any tasks have been added to any stages, False otherwise"""

        return not bool([x for x in self._stages.keys() if self._stages[x]['tasks']])

    def generate(self):
        """Build a tasklist from the queued stages"""

        if self.is_empty():
            self.log.warning('Tasklist is empty')
        else:
            self.log.info(self.name)

        # Finalize stage names
        for stage_name in self.stages():

            # Remove everything after | character
            if '|' in stage_name:
                new_name = self.get(stage_name, 'name')[:stage_name.index('|')]
                self.set(stage_name, name=new_name)

            # Append host list
            hostlist = self._stages[stage_name].pop('hosts', None)
            if hostlist:
                new_name = self.get(stage_name, 'name') + ' on {0}'.format(', '.join(hostlist))
                self.set(stage_name, name=new_name)

        # Get pre/post/untagged tasks
        pre = [x for x in self._stage_order if x in self._pre_order]
        post = [x for x in self._stage_order if x in self._post_order]
        main = [x for x in self._stage_order if not x in pre + post]

        # Reorder stages that have been tagged as pre or post
        stages = [self._stages[x] for x in pre + main + post if self._stages[x]['tasks']]

        return { 'name': self.name, 'stages': stages }

    def _exists_or_die(self, stage_name):

        if not stage_name in self._stages:
            raise DeployerException('No such stage has been defined: {0}'.format(stage_name))
