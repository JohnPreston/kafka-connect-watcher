class MockClusterConfig:
    def __init__(self):
        self.name = "cluster_config_name"


class MockEvaluationRule:
    def __init__(self, ignore_paused=True, ignore_unassigned=False):
        self.ignore_paused = ignore_paused
        self.ignore_unassigned = ignore_unassigned


class MockConnectCluster:
    def __init__(self):
        self.name = "connect_cluster_name"
        self.metrics = {"connectors": {}}


class MockTask:
    def __init__(self, state="RUNNING"):
        self.state = state

    def is_running(self):
        if self.state == "RUNNING":
            return True
        else:
            return False


class MockConnector:
    def __init__(self, state="RUNNING", name="mock-connector-name", tasks=[MockTask()]):
        self.cluster = MockConnectCluster()
        self.name = name
        self.state = state
        self.tasks = tasks
