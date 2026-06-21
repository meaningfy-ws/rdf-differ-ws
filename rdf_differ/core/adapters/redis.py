from typing import cast

import redis

from rdf_differ import config

# Fail-fast socket timeouts (seconds): a down Redis must not hang the
# CLI/API on connect or read (#133 hardening). A small constant is enough;
# we deliberately avoid inventing new config plumbing.
REDIS_SOCKET_TIMEOUT = 5

redis_client = redis.Redis(
    host=config.RDF_DIFFER_REDIS_LOCATION.split("redis://")[1],
    port=int(config.RDF_DIFFER_REDIS_PORT),
    socket_connect_timeout=REDIS_SOCKET_TIMEOUT,
    socket_timeout=REDIS_SOCKET_TIMEOUT,
)

REVOKING_QUEUE = "revoke"


def push_task_to_queue(
    task_id: str, queue: str = REVOKING_QUEUE, client: redis.Redis | None = None
):
    """
    used for adding a task's id to a queue to be "undone" or cancelled.

    :param task_id: celery task id
    :param queue: depending on the type of action you take use different queue
    :param client: redis client
    """
    client = client if client else redis_client
    client.lpush(queue, task_id)


def remove_task_from_queue(
    task_id: str, queue: str = REVOKING_QUEUE, client: redis.Redis | None = None
) -> bool:
    """
    "cancel the cancellation" of a task from the specified queue

    :param task_id: celery task id
    :param queue: depending on the type of action you take use different queue
    :param client: redis client
    :return: if item was found and removed from queue return true otherwise false
    """
    client = client if client else redis_client

    return bool(client.lrem(queue, 1, task_id))


def task_exists_in_queue(
    task_id: str, queue: str = REVOKING_QUEUE, client: redis.Redis | None = None
) -> bool:
    """
    check if task is in specified queue
    :param task_id: celery task id
    :param queue: depending on the type of action you take use different queue
    :param client: redis client
    :return: if item was found return true otherwise false
    """
    client = client if client else redis_client

    queue_list = cast(list, client.lrange(queue, 0, -1))

    return any(item.decode() == task_id for item in queue_list)
