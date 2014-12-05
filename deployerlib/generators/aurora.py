import os
import urllib2

from deployerlib.log import Log
from deployerlib.generator import Generator
from deployerlib.exceptions import DeployerException


class AuroraGenerator(Generator):
    """Aurora task list generator"""

    def generate(self):
        """Build the task list"""

        packages = self.get_packages()
        if not self.config.redeploy:
            remote_versions = self.get_remote_versions(packages)

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
            deploy_info += ', to hosts {0}'.format(','.join(hosts))
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
        deploy_tasks = []
        remove_temp_tasks = []

        for package in packages:

            servicename = package.servicename
            service_config = self.config.get_with_defaults('service', servicename)
            hosts = self.config.get_service_hosts(servicename)

            for hostname in hosts:

                if not self.config.redeploy and remote_versions.get(servicename).get(hostname) \
                  == package.version:
                    self.log.info('version is up to date on {0}, skipping'.format(hostname), tag=servicename)
                    continue

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
                  'destination': os.path.join(service_config.install_location, service_config.unpack_dir),
                })

                if service_config.control_type == 'props':
                    props_tasks.append({
                      'tag': servicename,
                      'command': 'deploy_properties',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': '{0}/*'.format(os.path.join(service_config.install_location,
                          service_config.unpack_dir, package.packagename, self.config.environment)),
                      'destination': '{0}/'.format(service_config.properties_location),
                      'version': package.version,
                    })

                if service_config.control_type == 'daemontools':
                    deploy_task = {
                      'tag': servicename,
                      'command': 'deploy_and_restart',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': os.path.join(service_config.install_location, service_config.unpack_dir, package.packagename),
                      'destination': os.path.join(service_config.install_location, package.packagename),
                      'link_target': os.path.join(service_config.install_location, servicename),
                    }

                    if hasattr(service_config, 'migration_command') and not [x for x in dbmig_tasks \
                      if x['tag'] == servicename]:

                        self.log.info('Adding DB migrations to be run on {0}'.format(hostname), tag=servicename)

                        dbmig_tasks.append({
                          'tag': servicename,
                          'command': 'dbmigration',
                          'remote_host': hostname,
                          'remote_user': self.config.user,
                          'source': service_config.migration_command.format(
                              migration_location=os.path.join(service_config.install_location, service_config.unpack_dir, package.packagename,
                                  'db/migrations'),
                              migration_options='',
                              properties_location=service_config.properties_location,
                              ),
                          })

                    if '.' in servicename:
                        shortservicename = servicename.rsplit(".", 1)[1].replace("-server", "")
                    else:
                        shortservicename = service

                    if '.' in hostname:
                        shorthostname = hostname.split(".", 1)[0]
                    else:
                        shorthostname = hostname

                    if hasattr(service_config, 'lb_service'):
                        lb_service = service_config.lb_service.format(
                                hostname=shorthostname,
                                servicename=shortservicename,
                                )
                    else:

                        if self.config.environment == "production":
                            lb_service = self.config.platform + "_" +  shortservicename + "_" +  hostname.split(".", 1)[0] + "." + self.config.platform
                        elif self.config.environment == "lp":
                            lb_service = self.config.platform + "_" +  shortservicename + "_" +  hostname.split(".", 1)[0] + "." + self.config.platform + self.config.environment
                        else:
                            lb_service = self.config.platform + "_" +  shortservicename + "_" +  hostname.split(".", 1)[0]

                        self.log.info('Generated lb_service={0}'.format(repr(lb_service)))

                    lb_hostname, lb_username, lb_password = self.config.get_lb(servicename, hostname)

                    if lb_hostname and lb_username and lb_password:
                        deploy_task['lb_service'] = lb_service

                        deploy_task.update({
                          'lb_hostname': lb_hostname,
                          'lb_username': lb_username,
                          'lb_password': lb_password,
                        })

                    else:
                        self.log.warning('No load balancer found for service on {0}'.format(hostname), tag=servicename)

                    for option in ('control_timeout', 'lb_timeout'):
                        if hasattr(service_config, option):
                            deploy_task[option] = getattr(service_config, option)

                    for cmd in ['stop_command', 'start_command', 'check_command']:

                        if hasattr(service_config, cmd):
                            deploy_task[cmd] = service_config[cmd].format(
                              servicename=servicename,
                              port=service_config['port'],
                            )
                        else:
                            self.log.warning('No {0} configured'.format(cmd), tag=servicename)

                    deploy_tasks.append(deploy_task)

                if not [x for x in create_temp_tasks if x['remote_host'] == hostname and \
                  x['source'] == os.path.join(service_config.install_location, service_config.unpack_dir)]:
                    create_temp_tasks.append({
                      'command': 'createdirectory',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': os.path.join(service_config.install_location, service_config.unpack_dir),
                      'clobber': True,
                    })

                    remove_temp_tasks.append({
                      'command': 'removefile',
                      'remote_host': hostname,
                      'remote_user': self.config.user,
                      'source': os.path.join(service_config.install_location, service_config.unpack_dir),
                    })
            # end for hostname in hosts:
        # end for package in packages:

        if not upload_tasks and not unpack_tasks and not deploy_tasks:
            self.log.info('No services require deployment')
            return

        if props_tasks or dbmig_tasks or deploy_tasks:
            doing_deploy_tasks = True
        else:
            doing_deploy_tasks = False

        if upload_tasks:
            task_list['stages'].append({
              'name': 'Upload',
              'concurrency': 10,
              'concurrency_per_host': 5,
              'tasks': upload_tasks,
            })

        if create_temp_tasks:
            task_list['stages'].append({
              'name': 'Create temp directories',
              'concurrency': 10,
              'concurrency_per_host': 5,
              'tasks': create_temp_tasks,
            })

        if unpack_tasks:
            task_list['stages'].append({
              'name': 'Unpack',
              'concurrency': 10,
              'concurrency_per_host': 3,
              'tasks': unpack_tasks,
            })

        if doing_deploy_tasks and self.config.release:
            if hasattr(self.config, 'pipeline_url'):
                if self.config.platform == 'aurora':
                    if not (self.config.categories or self.config.hosts or self.config.hostgroups) or self.config.pipeline_start:
                        task_list['stages'].append(self.get_pipeline_notify_stage('deploying', deploy_release))

            if hasattr(self.config, 'graphite'):
                if not (self.config.categories or self.config.hosts or self.config.hostgroups) or self.config.pipeline_start:
                    task_list['stages'].append(self.get_graphite_stage('start'))

        if props_tasks:
            task_list['stages'].append({
              'name': 'Deploy properties for environment {0}'.format(self.config.environment),
              'concurrency': 10,
              'tasks': props_tasks,
            })

        if dbmig_tasks:
            task_list['stages'].append({
              'name': 'Database migrations',
              'concurrency': 1,
              'tasks': dbmig_tasks,
            })

        for servicenames in self.config.deployment_order:

            if isinstance(servicenames, basestring):
                servicenames = [servicenames]

            this_stage = [x for x in deploy_tasks if x['tag'] in servicenames]

            if not this_stage:
                self.log.debug('No deployment tasks for service(s) {0}'.format(', '.join(servicenames)))
                continue

            deploy_tasks = [x for x in deploy_tasks if not x in this_stage]

            to_deploy = []
            for x in this_stage:
                if x['tag'] not in to_deploy:
                    to_deploy.append(x['tag'])

            task_list['stages'].append({
              'name': 'Deploy {0}'.format(', '.join(to_deploy)),
              'concurrency': 3,
              'tasks': this_stage,
            })

        if doing_deploy_tasks and self.config.release:
            if hasattr(self.config, 'pipeline_url'):
                if self.config.platform == 'aurora':
                    if not (self.config.categories or self.config.hosts or self.config.hostgroups) or self.config.pipeline_end:
                        task_list['stages'].append(self.get_pipeline_notify_stage('deployed', deploy_release))
                        if self.config.environment == 'demo':
                            task_list['stages'].append(self.get_pipeline_upload_stage(deploy_release))

            if hasattr(self.config, 'graphite'):
                if not (self.config.categories or self.config.hosts or self.config.hostgroups) or self.config.pipeline_end:
                    task_list['stages'].append(self.get_graphite_stage('end'))

        if remove_temp_tasks:
            task_list['stages'].append({
              'name': 'Remove temp directories',
              'concurrency': 10,
              'tasks': remove_temp_tasks,
            })

        if deploy_tasks:
            leftovers = set([x['tag'] for x in deploy_tasks])
            raise DeployerException('Leftover tasks - services not specified in deployment order? {0}'.format(
              ', '.join(leftovers)))

        return task_list

    def uploadPackageToPipeline(self, package):

        if not 'pipeline_url' in self.config:
            self.log.error('pipeline_url is missing in config')
            return False

        projects = []
        deploy_package_dir = "/opt/deploy_packages/%s" % (package)
        try:
            for fileName in os.listdir(deploy_package_dir):
                if re.match(".*_(.*-){3}.*(tar.gz|.war)", fileName):
                    suffix = fileName.split("_")[0]
                    sp = fileName.split("-")
                    projects.append({'project' : suffix, 'hash' : sp[len(sp) - 2]})

            req = urllib2.Request('{0}/package/{1}/projects'.format(self.config.pipeline_url,package))
            req.add_header('Content-Type', 'application/json')
            urllib2.urlopen(req, json.dumps({'projects' : projects}))
        except OSError as e:
            self.log.warning("Deployment packages directory %s not present: %s" % (deploy_package_dir, e.strerror))
            pass # Ignore the error for now, propably the directory does not exist


    def notifyPipeline(self, status, package):

        if not 'pipeline_url' in self.config:
            self.log.error('pipeline_url is missing in config')
            return False

        envt = self.config.environment
        if envt == "production":
            envt = "prod"

        url = '%s/%s/%s/%s' % (self.config.pipeline_url, status, envt, package)

        self.log.info("Calling %s on pipeline..." % url)

        if 'proxy' in self.config:
            proxy_support = urllib2.ProxyHandler({ "http" : self.config.proxy })
            opener = urllib2.build_opener(proxy_support)
        else:
            opener = urllib2.build_opener()

        try:
            opener.open(url)
            return True
        except:
            return False

