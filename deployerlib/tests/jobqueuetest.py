#! /usr/bin/env python

import unittest

from multiprocessing import Process, Manager

from deployerlib.log import Log
from deployerlib.config import Config
from deployerlib.tasklist import Tasklist
from deployerlib.jobqueue import JobQueue
from deployerlib.exceptions import DeployerException
from deployerlib.commands import testcommand


class JobQueueTest(unittest.TestCase):

    def setUp(self):
        self.log = Log(self.__class__.__name__)

        config = Config()
        builder = Tasklist(config, generator_name='test')
        manager = Manager()
        self.results = manager.dict()
        self.job_list = []

        for message in ('test1', 'test2', 'test3'):
            command = testcommand.TestCommand(message=message)
            process = Process(target=command.thread_execute, name=repr(command), args=[repr(command), self.results])
            process._host = message
            self.job_list.append(process)

    def testSerial(self):
        self.log.info('Testing serial execution')
        self.results.clear()

        job_queue = JobQueue(self.results, 1, 1)
        job_queue.append(self.job_list)
        job_queue.close()

        self.assertTrue(job_queue.run())

    def testConcurrent(self):
        self.log.info('Testing concurrent execution')
        self.results.clear()

        job_queue = JobQueue(self.results, 5, 5)
        job_queue.append(self.job_list)
        job_queue.close()

        self.assertTrue(job_queue.run())


if __name__ == '__main__':
    unittest.main()
