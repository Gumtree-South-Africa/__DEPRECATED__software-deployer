import os
import urllib2

from deployerlib.log import Log
from deployerlib.generator import Generator
from deployerlib.exceptions import DeployerException


class RbbGenerator(Generator):
    """RBB task list generator"""

    def generate(self):
        """Build the task list"""

        # helper function:
        def generate_to_deploy_list(tasklist):
            """ Extracts from a tasklist for each tag the remote_host and generates
                a list of strings like '<taglist> to hosts <hostlist>'
            """
            to_deploy_to = {}
            for x in tasklist:
                s = x['tag']
                h = x['remote_host']
                if s not in to_deploy_to:
                    to_deploy_to[s] = []
                to_deploy_to[s].append(h)

            sh_lists = []
            for (s,hlist) in to_deploy_to.items():
                found = 0
                for (sl,hl) in sh_lists:
                    if set(hl) == set(hlist):
                        sh_lists.remove((sl,hl))
                        sl.append(s)
                        sh_lists.append((sl,hl))
                        found = 1
                        break
                if not found:
                    sh_lists.append(([s],hlist))

            to_deploy = []
            for (slist,hlist) in sh_lists:
                to_deploy.append(','.join(slist) + ' to hosts ' + ','.join(hlist))

            return to_deploy


        # main part of generate
        packages = self.get_packages()
        if not self.config.redeploy:
            remote_versions = self.get_remote_versions(packages,
                    concurrency=self.config.non_deploy_concurrency,
                    concurrency_per_host=self.config.non_deploy_concurrency_per_host,
                    abort_on_error=True)

            #print 'returned remote_versions: {0}'.format(remote_versions)

        if not self.config.redeploy and not remote_versions:
            raise DeployerException('Errors with determining remote versions')

        if self.config.release:
            if type(self.config.release) is list:
                if len(self.config.release) > 1:
                    self.log.critical('No support for multiple release directories')
                    raise DeployerException('No support for multiple release directories')
                else:
                    self.config.release = self.config.release[0]

            if type(self.config.release) is not str:
                raise DeployerException('{0} is of type {1}, should be {2}'.format(repr(self.config.release),repr(type(self.config.release)),
                    repr(str)))

            deploy_release = filter(None, self.config.release.split("/"))[-1]
            if self.config.platform in deploy_release:
                deploy_release = deploy_release.replace("%s-" % self.config.platform, "")
            deploy_info = 'release {0}'.format(repr(deploy_release))
        elif self.config.component:
            deploy_info = 'component(s) {0}'.format(','.join(self.config.component))

        if self.config.hosts:
            deploy_info += ', to hosts {0}'.format(','.join(self.config.hosts))
        elif self.config.hostgroups:
            deploy_info += ', to hostgroups {0}'.format(','.join(self.config.hostgroups))
        elif self.config.categories:
            if type(self.config.categories) is str:
                deploy_info += ', to cluster {0}'.format(self.config.categories)
            else:
                deploy_info += ', to categories {0}'.format(','.join(self.config.categories))

        task_list = {
          'name': 'Aurora deployment of platform {0}, environment {1}, {2}'.format(self.config.platform, self.config.environment, deploy_info),
          'stages': [],
        }

        upload_tasks = []
        create_temp_tasks = []
        unpack_tasks = []
        props_tasks = []
        dbmig_tasks = []
        deploy_tasks = {}
        cleanup_tasks = []

        for package in packages:

            servicename = package.servicename

            service_config = self.config.get_with_defaults('service', servicename)
            if not service_config:
                self.log.critical('No service config found for service {0}'.format(repr(servicename)))
                raise DeployerException('No service config found for service {0}'.format(repr(servicename)))

            service_config.unpack_location = os.path.join(service_config.install_location, service_config.unpack_dir)

            if hasattr(self.config, 'restrict_to_hostgroups') and self.config.restrict_to_hostgroups and self.config.force:
                hostgroups = self.config.restrict_to_hostgroups
            elif hasattr(self.config, 'restrict_to_hosts') and self.config.restrict_to_hosts and self.config.force:
                hostgroups = [None]
            else:
                if 'hostgroups' in service_config:
                    hostgroups = service_config.hostgroups
                else:
                    raise DeployerException('No hostgroups specified in config where to deploy service {0}'.format(repr(servicename)))

            for hostgroup in hostgroups:
                hosts = self.config.get_service_hosts(servicename, hostgroup)

                num_sub_stages = 1
                if hostgroup and hasattr(service_config, 'min_nodes_up') and service_config.min_nodes_up > 0:
                    num_nodes_in_group = self.config.get_num_hosts_in_hostgroup(hostgroup)
                    max_nodes_down = num_nodes_in_group - service_config.min_nodes_up
                    if max_nodes_down <= 0:
                        if self.config.force:
                            self.log.warning(
                                    'min_nodes_up is set to {0}, but number of nodes in group {1} is {2}. Forcing deployment because of --force'.format(
                                        service_config.min_nodes_up, hostgroup, num_nodes_in_group))
                        else:
                            raise DeployerException('min_nodes_up is set to {0}, but number of nodes in group {1} is {2}'.format(
                                service_config.min_nodes_up, hostgroup, num_nodes_in_group))
                    else:
                        num_div_max = num_nodes_in_group / max_nodes_down
                        num_mod_max = num_nodes_in_group % max_nodes_down
                        if num_mod_max > 0:
                            num_sub_stages = num_div_max + 1
                        else:
                            num_sub_stages = num_div_max

                host_no = -1
                for hostname in hosts:

                    host_no += 1
                    if not self.config.redeploy:
                        service_versions = remote_versions.get(servicename)
                        remote_version = service_versions.get(hostname)
                    else:
                        remote_version = 'UNDETERMINED'

                    if remote_version == package.version:
                        self.log.info('version is up to date on {0}, skipping'.format(hostname), tag=servicename)
                        continue

                    if remote_version in ['NOT_INSTALLED_NOT_IN_DAEMONTOOLS']:
                        self.log.info('Service has been found to be not installed/configured on {0}, skipping'.format(hostname), tag=servicename)
                        continue

                    self.log.info('Will replace version {0} with {1} on {2}'.format(remote_version, package.version, hostname), tag=servicename)

                    upload_tasks.append({
                      'tag': servicename,
                      'command': 'upload',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': package.fullpath,
                      'destination': service_config.destination,
                    })

                    unpack_tasks.append({
                      'tag': servicename,
                      'command': 'unpack',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': os.path.join(service_config.destination, package.filename),
                      'destination': service_config.unpack_location,
                    })

                    # cleanup upload directory
                    cleanup_tasks.append({
                      'command': 'cleanup',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'path': service_config.destination,
                      'filespec': '{0}_*'.format(package.servicename),
                      'keepversions': self.config.keep_versions,
                      'exclude': package.filename,
                      'tag': package.servicename,
                    })

                    # cleanup unpack directory
                    cleanup_tasks.append({
                      'command': 'cleanup',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'path': service_config.unpack_location,
                      'filespec': '{0}_*'.format(package.servicename),
                      'keepversions': 0,
                      'exclude': 'XXXXXXX', # deliberately setting to a string that will never match
                      'tag': package.servicename,
                    })

                    # cleanup webapps directory
                    cleanup_tasks.append({
                      'command': 'cleanup',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'path': service_config.install_location,
                      'filespec': '{0}_*'.format(package.servicename),
                      'keepversions': self.config.keep_versions,
                      'exclude': package.packagename,
                      'tag': package.servicename,
                    })

                    deploy_task = {
                      'tag': servicename,
                      'command': 'deploy_and_restart',
                      'check_daemontools': False,
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': package.get_install_path(service_config.unpack_location),
                      'destination': package.get_install_path(service_config.install_location),
                      'link_target': package.get_link_path(service_config.install_location),
                      'check_registered': True,
                    }

                    if hasattr(service_config, 'migration_command') and not [x for x in dbmig_tasks \
                      if x['tag'] == servicename]:

                        self.log.info('Adding DB migrations to be run on {0}'.format(hostname), tag=servicename)

                        dbmig_location = os.path.join(service_config.unpack_location, package.packagename)

                        dbmig_tasks.append({
                          'tag': servicename,
                          'command': 'dbmigration',
                          'if_exists': dbmig_location,
                          'remote_host': hostname,
                          'remote_user': self.config.user,
                          'source': service_config.migration_command.format(
                              migration_location=dbmig_location,
                              migration_options='',
                              properties_location=service_config.properties_location,
                              ),
                          })

                    lb_hostname, lb_username, lb_password = self.config.get_lb(servicename, hostname)

                    if not self.config.ignore_lb and lb_hostname and lb_username and lb_password:

                        if hasattr(service_config, 'lb_service'):

                            deploy_task['lb_service'] = self.config.get_lb_servicename(servicename, hostname, service_config.lb_service)

                            deploy_task.update({
                                'lb_hostname': lb_hostname,
                                'lb_username': lb_username,
                                'lb_password': lb_password,
                            })

                        else:
                            self.log.warning('No load balancer found for service on {0}'.format(hostname), tag=servicename)

                    else:
                        self.log.info('Not doing lb control because of ignore_lb option or loadbalancer configuration is absent', tag=servicename)

                    for option in ('control_timeout', 'lb_timeout'):
                        if hasattr(service_config, option):
                            deploy_task[option] = getattr(service_config, option)

                    for cmd in ['stop_command', 'start_command', 'check_command', 'reload_command']:

                        if hasattr(service_config, cmd):
                            deploy_task[cmd] = service_config[cmd].format(
                              servicename=servicename,
                              port=service_config['port'],
                            )
                        else:
                            self.log.warning('No {0} configured'.format(cmd), tag=servicename)

                    sub_stage = repr(host_no % num_sub_stages)
                    if sub_stage not in deploy_tasks:
                        deploy_tasks[sub_stage] = []
                    deploy_tasks[sub_stage].append(deploy_task)

                    if not [x for x in create_temp_tasks if x['remote_host'] == hostname and \
                      x['source'] == service_config.unpack_location]:
                        create_temp_tasks.append({
                          'command': 'createdirectory',
                          'remote_host': hostname,
                          'remote_user': self.config.user,
                          'source': service_config.unpack_location,
                          'clobber': False,
                        })

                # end for hostname in hosts:
            # end for hg in hostgroups:
        # end for package in packages:

        if not upload_tasks and not unpack_tasks and not deploy_tasks:
            self.log.info('No services require deployment')
            return

        if props_tasks or dbmig_tasks or deploy_tasks:
            doing_deploy_tasks = True
        else:
            doing_deploy_tasks = False

        if doing_deploy_tasks and self.config.release:
            if hasattr(self.config, 'pipeline_url'):
                if self.config.platform == 'aurora':
                    if not (self.config.categories or self.config.hosts or self.config.hostgroups) or self.config.pipeline_start:
                        task_list['stages'].append(self.get_pipeline_notify_stage('deploying', deploy_release))

            if hasattr(self.config, 'graphite'):
                if not (self.config.categories or self.config.hosts or self.config.hostgroups) or self.config.pipeline_start:
                    task_list['stages'].append(self.get_graphite_stage('start'))

        if upload_tasks:
            task_list['stages'].append({
              'name': 'Upload',
              'concurrency': self.config.non_deploy_concurrency,
              'concurrency_per_host': self.config.non_deploy_concurrency_per_host,
              'tasks': upload_tasks,
            })

        if create_temp_tasks:
            task_list['stages'].append({
              'name': 'Create temp directories',
              'concurrency': self.config.non_deploy_concurrency,
              'concurrency_per_host': self.config.non_deploy_concurrency_per_host,
              'tasks': create_temp_tasks,
            })

        if unpack_tasks:
            task_list['stages'].append({
              'name': 'Unpack',
              'concurrency': self.config.non_deploy_concurrency,
              'concurrency_per_host': self.config.non_deploy_concurrency_per_host,
              'tasks': unpack_tasks,
            })

        if props_tasks:
            to_deploy = generate_to_deploy_list(props_tasks)
            self.log.info('Adding stage to deploy {0}'.format(', '.join(to_deploy)))
            task_list['stages'].append({
              'name': 'Deploy properties for environment {0}'.format(self.config.environment),
              'concurrency': self.config.non_deploy_concurrency,
              'tasks': props_tasks,
            })

        if dbmig_tasks:
            #to_run = generate_to_deploy_list(dbmig_tasks)
            #self.log.info('Adding stage with dbmigrations for {0}'.format(', '.join(to_run).replace('to hosts','to be run on hosts')))
            task_list['stages'].append({
              'name': 'Database migrations',
              'concurrency': 1,
              'tasks': dbmig_tasks,
            })

        for servicenames in self.config.deployment_order:

            if isinstance(servicenames, basestring):
                servicenames = [servicenames]

            for sub_stage in sorted(deploy_tasks.keys()):
                this_stage = [x for x in deploy_tasks[sub_stage] if x['tag'] in servicenames]

                if not this_stage:
                    self.log.debug('No deployment tasks for service(s) {0} in sub_stage {1}'.format(', '.join(servicenames), sub_stage))
                    continue

                deploy_tasks[sub_stage] = [x for x in deploy_tasks[sub_stage] if not x in this_stage]

                to_deploy = generate_to_deploy_list(this_stage)

                self.log.info('Adding stage to deploy {0}'.format(', '.join(to_deploy)))
                task_list['stages'].append({
                  'name': 'Deploy {0}'.format(', '.join(to_deploy)),
                  'concurrency': self.config.deploy_concurrency,
                  'concurrency_per_host': self.config.deploy_concurrency_per_host,
                  'tasks': this_stage,
                })

        if cleanup_tasks:
            task_list['stages'].append({
              'name': 'Cleanup',
              'concurrency': self.config.non_deploy_concurrency,
              'concurrency_per_host': self.config.non_deploy_concurrency_per_host,
              'tasks': cleanup_tasks,
            })

        if doing_deploy_tasks:
            archive_stage = self.get_archive_stage()
            if archive_stage:
                task_list['stages'].append(archive_stage)

            if self.config.release:
                if hasattr(self.config, 'pipeline_url'):
                    if self.config.platform == 'aurora':
                        if not (self.config.categories or self.config.hosts or self.config.hostgroups) or self.config.pipeline_end:
                            task_list['stages'].append(self.get_pipeline_notify_stage('deployed', deploy_release))
                            if self.config.environment == 'demo':
                                task_list['stages'].append(self.get_pipeline_upload_stage(deploy_release))

                if hasattr(self.config, 'graphite'):
                    if not (self.config.categories or self.config.hosts or self.config.hostgroups) or self.config.pipeline_end:
                        task_list['stages'].append(self.get_graphite_stage('end'))

        leftovers = set()
        for sub_stage in deploy_tasks.keys():
            if deploy_tasks[sub_stage]:
                leftovers = leftovers.union(set([x['tag'] for x in deploy_tasks[sub_stage]]))
        if leftovers:
            raise DeployerException('Leftover tasks - services not specified in deployment order? {0}'.format(
              ', '.join(leftovers)))

        return task_list

