from hexrepo_task.interactor.event.app import TaskApp

from ..dependencies import get_queue_uow, get_task_queue

app = TaskApp(get_uow=get_queue_uow, get_queue=get_task_queue)
