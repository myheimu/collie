"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import datetime

from django.test import TestCase
from project.flows import Flow, Job, ExecutionOptions


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


class TestFlow(TestCase):
    def test_parse_flow_to_json(self):
        jobs = list()

        job1 = Job()
        job1.job_id = 'job1'
        job1.job_type = 'java'
        job1.job_source = 'job1.job'
        job1.children = ['job2', 'job3']
        jobs.append(job1)

        job2 = Job()
        job2.job_id = 'job2'
        job2.job_type = 'java'
        job2.job_source = 'job2.job'
        job2.children = ['job3']
        job2.ancestors = ['job1']
        jobs.append(job2)

        job3 = Job()
        job3.job_id = 'job3'
        job3.job_type = 'java'
        job3.job_source = 'job3.job'
        job3.ancestors = ['job1', 'job2']
        jobs.append(job3)

        execution = ExecutionOptions()
        execution.failure_emails = ['1@xiaomi.com', '2@xiaomi.com']
        execution.flow_parameters = {'param1': 'para1Value'}

        flow = Flow()
        flow.node_id = 1
        flow.execution_id = 1000
        flow.project_id = 1
        flow.project_version = 1
        flow.submit_user = "shixin"
        flow.submit_time = str(datetime.datetime.today())
        flow.flow_id = "test1"
        flow.flow_status = "READY"
        flow.jobs = jobs
        flow.execution_options = execution

        print flow.dump_to_json()
