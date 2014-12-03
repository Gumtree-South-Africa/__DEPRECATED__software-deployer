Software Deployer
==

Goal
--
A modular, extendable, configuration-driven deployment system.

How it works
--
A Generator class creates a list of tasks to be executed. The list of tasks is passed to an Executor. The Executor runs the task list. Each task is defined in a Command.

Here is an example of a top-level script:

```python
from deployerlib.commandline import CommandLine
from deployerlib.config import Config
from deployerlib.tasklist import Tasklist
from deployerlib.executor import Executor
from deployerlib.exceptions import DeployerException

args = CommandLine()
config = Config(args)
builder = Tasklist(config, 'TestGenerator')
executor = Executor(tasklist=builder.tasklist)

try:
    executor.run()
except DeployerException as e:
    print 'Execution failed: {0}'.format(e)
```

Generators
--
The Generator is specific to a platform. A new Generator can be created by inheriting from the Generator class. A Generator has access to options specified in the configuration file and on the command line. It will provide its functionality by overriding the _generate()_ method, and will return a JSON-formatted list of stages. Stages are executed serially in the order listed. Each stage contains a list of tasks which can be executed concurrently.

Generators inherit the following methods:

- get_packages(): Gets a list of components as specified on the command line and returns a list of Package objects.
- get_remote_versions(list_of_package_objects): Get the versions of packages running on remote hosts. Returns a dict of package versions, i.e. remote_versions[servicename][hostname]
- get_graphite_stage(metric_suffix): Returns a tasklist stage that calls the send_graphite command.

Here is an example of a basic Generator:

```python
from deployerlib.generator import Generator


class TestGenerator(Generator):

    def generate(self):

        self.log.info('Generating test task list')

        task = {
          'command': 'test_command',
          'message': 'Hello World',
        }

        stage = {
          'name': 'Test stage',
          'concurrency': 1,
          'tasks': [task],
        }

        tasklist = {
          'name': 'Test Generator',
          'stages': [stage],
        }

        return tasklist
```

Configuration files
--
A configuration file is in YAML format. Currently the only absolute requirement of the config file is a *platform* variable. This specifies which generator will be used.

The configuration file may contain environment-specific configuration such as a list of services to be deployed and a list of hosts to deploy them to. It may also contain details such as login information for remote devices and information on how to control services. The configuration file is specified by the user via the --config command-line option. The contents of the config file are merged with the command line options and presented to the Generator as the _self.config_ object.

Here is an example of a basic configuration file:

```yaml
platform: test

hostgroup:

    frontend:
    - fe001
    - fe002
    backend:
    - be001
    - be002

service:

    web1-frontend:
        hosts: [frontend]
        port: 8080

    worker1-backend:
        hosts: [backend]
        port: 8000
```

Commands
--
Commands are called in a task using the special *command* keywoard. The value of *command* will resolve to a class in deployerlib.commands. Each of these classes perform an individual task, typically on a remote host.

Commands inherit the Command class and override the _execute()_ method. It is also recommended to override the _initialize()_ method, at minimum in order to verify the arguments that are passed to the class. Verifying input using the _initalize()_ class allows the Executor to verify the syntax of a task list without having to execute it. This is useful for testing a Generator or configuration file by doing a dry run.

The _initialize()_ method may also provide further initialization steps, such as setting additional attributes or defaults.

Both the _initialize()_ and _execute()_ methods must return a value that resolves to *True* if execution is to continue. If _initialize()_ doesn't return a true value then the command will fail to initialize, which means a dry run will report a failure and execution will not be started. If _execute()_ doesn't return a true value then the Exectutor will abort the job queue.

Note that unhandled exceptions occuring within either _initialize()_ or _execute()_ will also result in execution being halted.

Here is an example of a basic Command:

```python
from deployerlib.command import Command


class TestCommand(Command):

    def initialize(self, message, optional_argument=None):
        # Accepting an optional argument means the attribute must be set
        # by initialize().
        self.optional_argument = optional_argument
        self.log.info('Initializing test command: {0} / {1}'.format(
          message, optional_argument))

        return True

    def execute(self):
        self.log.info('Executing test command: {0} / {1}'.format(
          self.message, self.optional_argument))

        return True
```

Remote Hosts
--
A remote host object is created from a task via the special *remote_host* keyword. The value of *remote_host* (and optionally *remote_user*) will be used to create a RemoteHost object. RemoteHost objects are passed to Commands and are used to execute tasks on remote servers. A RemoteHost object provides the following methods:

- put_remote(local_file, remote_dir): Upload a local file to a remote host. Returns the list of files that were uploaded.
- file_exists(remote_file): Check whether a file or directory exists on a remote host. Returns true or false.
- execute_remote(command, use_sudo=False): Execute a command on a remote host (optinally via sudo). Returns a fabric result object containing the output of the command as the string representation, as well as .failed and .succeeded attributes.

Execution
--
Full execution is provided by the _deploy.py_ top-level script. It will read the command line and config file, and will pass the results to a Generator. The task list created by the Generator is eventually passed to Executor, which uses the contents of the task list to instantiate the corresponding Commands. Execution can beging once all tasks have been instantiated as Commands.

Here is an example of a deploy command that will generate and execute a task list in one step:

```sh
deploy.py --config /etc/marktplaats/platform-aurora.conf --directory /opt/tarballs/aurora-198604260123
```

In normal execution, the deploy.py script will be used to run the Generator, parse a task list, and execute the generated task list. However it is also possible to create a task list in advance, either generated or by hand, and execute it directly.

Here is an example of a deploy command that will execute a pre-generated task list:

```sh
deploy.py --tasklist ~/tasklist.json
```

Dry run
--
It is possible to test the syntax of a task list by instantiating the Executor class. This is presented externally using the _build_tasklist.py_ top-level script. It requires the same arguments as deploy.py, namely --config and --component or --directory. Without additional commands it will symply end with "Syntax ok" if the Executor was able to parse the task list. It is also possible to view the task list by specifying --dump, or save the task list by specifying --save _filename_.

```sh
build_tasklist.py --config /etc/marktplaats/platform-aurora.conf --directory /opt/tarballs/aurora-198604260123 --save ~/tasklist.json
```

This functionality allows a user or developer to see exactly which tasks would be executed without having to make any changes to remote systems. A task list generated and saved in this way can also be executed directly using *deploy.py --tasklist _filename_*, further giving the possibility of editing a task list by hand before executing it.

JobQueue and concurrent execution
--
Concurrency is configured via two keywords provided in a stage:

- concurrency: The total number of tasks that can be executed in parallel
- concurrency_per_host: The maximum number of tasks that can be running at once on a single host

The JobQueue class is responsbile for managing the execution of tasks. A JobQueue is created by providing a list of Command objects which have been instantiated from a task list. JobQueue will start spawning jobs until it reaches one of the limits specified by concurrency or concurrency_per_host. As jobs complete, JobQueue will continue spawning new jobs, within the specified limits of concurrency, until no jobs are left in the queue.

If a job does not complete successfully (i.e. if a Command returns a result that resolves to None or False), then JobQueue will not start any new jobs. It will wait for for currently-running jobs to finish, then it will return False to its caller.

Example
--
The code snippets given above can be combined to make a working example. Here is the output of the top-level script, configuration file, generator and command given as examples in this document:

```sh
$ ./test.py --config test.conf
2014-12-03 15:29:01,868 [INFO    ] [Config         ] [*] [*] Loading configuration from test.conf
2014-12-03 15:29:01,873 [INFO    ] [TestGenerator  ] [*] [*] Generating test task list
2014-12-03 15:29:01,885 [INFO    ] [TestCommand    ] [*] [*] Initializing test command: Hello World / None
2014-12-03 15:29:01,886 [INFO    ] [Executor       ] [*] [*] Starting stage: Test stage
2014-12-03 15:29:01,891 [INFO    ] [TestCommand    ] [local] [*] Executing test command: Hello World / None
2014-12-03 15:29:01,909 [INFO    ] [Executor       ] [*] [*] Finished stage: Test stage
```
