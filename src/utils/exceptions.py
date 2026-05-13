class WorkflowHaltedException(Exception):
    """
    Raised when the workflow encounters a permanent failure or an explicit emergency stop.
    This exception must not be retried.
    """
    pass
