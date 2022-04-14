"""AWS Braket job."""
from datetime import datetime

from typing import List, Optional, Union

from braket.aws import AwsQuantumTask
from braket.tasks import GateModelQuantumTaskResult, QuantumTask
from qiskit.providers import JobV1, BackendV2
from qiskit.providers.models import BackendStatus
from qiskit.result import Result
from qiskit.result.models import ExperimentResult, ExperimentResultData


class AWSBraketJob(JobV1):
    """AWSBraketJob."""

    def __init__(
        self,
        job_id: str,
        backend: BackendV2,
        tasks: Union[List[QuantumTask]],
        **metadata: Optional[dict]
    ):
        """AWSBraketJob for local execution of circuits.

        Args:
            job_id: id of the job
            backend: Local simulator
            tasks: Executed tasks
            **metadata:
        """
        super().__init__(backend=backend, job_id=job_id, metadata=metadata)
        self._job_id = job_id
        self._backend = backend
        self._metadata = metadata
        self._tasks = tasks
        self._date_of_creation = datetime.now()

    @property
    def shots(self) -> int:
        """Return the number of shots.

        Returns:
            shots: int with the number of shots.
        """
        # TODO: Shots can be retrieved from tasks metadata  # pylint: disable=fixme
        return (
            self.metadata["metadata"]["shots"]
            if "shots" in self.metadata["metadata"]
            else 0
        )

    def submit(self):
        pass

    def result(self) -> Result:

        experiment_results: List[ExperimentResult] = []
        task: AwsQuantumTask

        # For each task the results is get and filled into an ExperimentResult object
        for task in self._tasks:
            result: GateModelQuantumTaskResult = task.result()
            counts = {
                k[::-1]: v for k, v in dict(result.measurement_counts).items()
            }  # convert to little-endian
            data = ExperimentResultData(counts=counts)
            experiment_result = ExperimentResult(
                shots=self.shots,
                success=task.state() == "COMPLETED",
                status=task.state(),
                data=data,
            )
            experiment_results.append(experiment_result)

        return Result(
            backend_name=self._backend,
            backend_version=1,
            job_id=self._job_id,
            qobj_id=0,
            success=self.status(),
            results=experiment_results,
        )

    def cancel(self):
        pass

    def status(self):
        status: str = self._backend.status
        backend_status: BackendStatus = BackendStatus(
            backend_name=self._backend.name,
            backend_version="",
            operational=False,
            pending_jobs=0,  # TODO  # pylint: disable=fixme
            status_msg=status,
        )
        if status in ("ONLINE", "AVAILABLE"):
            backend_status.operational = True
        elif status == "OFFLINE":
            backend_status.operational = False
        else:
            backend_status.operational = False
        return backend_status
