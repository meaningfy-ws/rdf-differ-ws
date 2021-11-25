from rdf_differ.adapters.redis import push_task_to_queue, remove_task_from_queue, \
    task_exists_in_queue
from tests.conftest import FakeRedisClient


def test_push_task_to_revoking_queue():
    client = FakeRedisClient()
    task_id = 'task_id'
    queue = 'queue'

    push_task_to_queue(task_id, queue, client)

    assert client.actions[0] == ('LEFT PUSH', queue, task_id)


def test_remove_task_from_revoking_queue():
    client = FakeRedisClient()
    task_id = 'task_id'
    queue = 'queue'

    remove_task_from_queue(task_id, queue, client)

    assert client.actions[0] == ('REMOVE VALUE FROM KEY', queue, 1, task_id)


def test_task_exists_in_revoking_queue_true():
    task_id = 'task_id'
    client = FakeRedisClient([task_id.encode()])
    queue = 'queue'

    exists = task_exists_in_queue(task_id, queue, client)

    assert exists
    assert client.actions[0] == ('GET LIST FROM KEY', queue, 0, -1)


def test_task_exists_in_revoking_queue_false():
    task_id = 'task_id'
    client = FakeRedisClient([])
    queue = 'queue'

    exists = task_exists_in_queue(task_id, queue, client)

    assert not exists
    assert client.actions[0] == ('GET LIST FROM KEY', queue, 0, -1)
