import json


class Flow:
    def __init__(self):
        self.node_id = None  # default: 1

        self.execution_id = None  # ExecutionFlow ID

        self.project_id = None  # Project ID
        self.project_version = None  # Project Version ID

        self.flow_id = None  # optional
        self.flow_status = 'READY'

        self.submit_user = None  # optional
        self.submit_time = None  # optional

        self.proxy_users = None  # optional
        self.jobs = None  # job list: description see below
        self.properties = None  # Map type: optional
        self.execution_options = None  # Options --> dump_to_json
        '''@type: ExecutionOptions'''

    def dump_to_json(self):
        data = dict()
        data['nodeId'] = self.node_id
        data['execId'] = self.execution_id
        data['projectId'] = self.project_id
        data['projectVersion'] = self.project_version
        data['flowId'] = self.flow_id
        data['flowStatus'] = self.flow_status
        data['submitUser'] = self.submit_user
        data['submitTime'] = str(self.submit_time)
        data['proxyUsers'] = self.proxy_users
        data['properties'] = self.properties

        if self.execution_options:
            data['executionOptions'] = self.execution_options.convert_to_dict()

        if self.jobs:
            jobs = dict()
            for job in self.jobs:
                jobs[job.job_id] = job.convert_to_dict()

            data['jobs'] = jobs

        return json.dumps(data)


class Job:
    def __init__(self):
        self.job_id = None  # job name
        self.job_type = None  # shell / java / command
        self.job_status = 'READY'
        self.ignore_failed = False
        self.job_source = None  # .job configuration file
        self.inherited_job_source = None  # optional
        self.delay = None  # default: 0
        self.ancestors = None  # dependency
        self.children = None  # optional

    def convert_to_dict(self):
        data = dict()
        data['jobId'] = self.job_id
        data['jobType'] = self.job_type
        data['jobStatus'] = self.job_status
        data['jobSource'] = self.job_source
        data['ignoreFailed'] = self.ignore_failed

        if self.inherited_job_source is not None:
            data['inheritedJobSource'] = self.inherited_job_source

        if self.delay is not None:
            data['delay'] = self.delay

        if self.ancestors is not None:
            data['ancestors'] = self.ancestors

        if self.children is not None:
            data['children'] = self.children
        return data


class ExecutionOptions:
    CONCURRENT_OPTION_SKIP = 'SKIP'
    CONCURRENT_OPTION_PIPELINE = 'PIPELINE'
    CONCURRENT_OPTION_IGNORE = 'IGNORE'

    FAILURE_ACTION_FINISH_CURRENTLY_RUNNING = 'FINISH_CURRENTLY_RUNNING'
    FAILURE_ACTION_CANCEL_ALL = 'CANCEL_ALL'
    FAILURE_ACTION_FINISH_ALL_POSSIBLE = 'FINISH_ALL_POSSIBLE'

    def __init__(self):
        self.pipeline_execution_id = None  # ExecutionFlow ID
        self.pipeline_level = None  # 1. Flow / 2. Job
        self.concurrent_option = ExecutionOptions.CONCURRENT_OPTION_IGNORE
        self.failure_action = ExecutionOptions.FAILURE_ACTION_FINISH_CURRENTLY_RUNNING
        self.flow_parameters = None  # optional : JVM parameters
        self.notify_on_first_failure = True
        self.notify_on_last_failure = False
        self.failure_emails = None
        self.success_emails = None
        self.failure_emails_override = False
        self.success_emails_override = False

    def convert_to_dict(self):
        data = dict()
        if self.pipeline_execution_id is not None:
            data['pipelineExecId'] = self.pipeline_execution_id
        if self.pipeline_level is not None:
            data['pipelineLevel'] = self.pipeline_level

        data['concurrentOption'] = self.concurrent_option
        data['failureAction'] = self.failure_action

        if self.flow_parameters is not None:
            data['flowParameters'] = self.flow_parameters

        data['notifyOnFirstFailure'] = self.notify_on_first_failure
        data['notifyOnLastFailure'] = self.notify_on_last_failure

        if self.success_emails is not None:
            data['successEmails'] = self.success_emails

        if self.failure_emails is not None:
            data['failureEmails'] = self.failure_emails

        data['successEmailsOverride'] = self.success_emails_override
        data['failureEmailsOverride'] = self.failure_emails_override

        return data

