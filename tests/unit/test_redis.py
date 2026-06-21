from rdf_differ.core.adapters.redis import (
    REDIS_SOCKET_TIMEOUT,
    push_task_to_queue,
    redis_client,
    remove_task_from_queue,
    task_exists_in_queue,
)
from tests.conftest import FakeRedisClient


def test_redis_client_has_failfast_socket_timeouts():
    """A down Redis must not hang the client on connect/read (#133 hardening)."""
    kwargs = redis_client.connection_pool.connection_kwargs

    assert kwargs.get("socket_connect_timeout") == REDIS_SOCKET_TIMEOUT
    assert kwargs.get("socket_timeout") == REDIS_SOCKET_TIMEOUT


def test_push_task_to_revoking_queue():
    client = FakeRedisClient()
    task_id = "task_id"
    queue = "queue"

    push_task_to_queue(task_id, queue, client)

    assert client.actions[0] == ("LEFT PUSH", queue, task_id)


def test_remove_task_from_revoking_queue():
    client = FakeRedisClient()
    task_id = "task_id"
    queue = "queue"

    remove_task_from_queue(task_id, queue, client)

    assert client.actions[0] == ("REMOVE VALUE FROM KEY", queue, 1, task_id)


def test_task_exists_in_revoking_queue_true():
    task_id = "task_id"
    client = FakeRedisClient([task_id.encode()])
    queue = "queue"

    exists = task_exists_in_queue(task_id, queue, client)

    assert exists
    assert client.actions[0] == ("GET LIST FROM KEY", queue, 0, -1)


def test_task_exists_in_revoking_queue_false():
    task_id = "task_id"
    client = FakeRedisClient([])
    queue = "queue"

    exists = task_exists_in_queue(task_id, queue, client)

    assert not exists
    assert client.actions[0] == ("GET LIST FROM KEY", queue, 0, -1)
