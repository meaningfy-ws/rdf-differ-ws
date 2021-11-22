import redis

from rdf_differ.config import RDF_DIFFER_REDIS_LOCATION, RDF_DIFFER_REDIS_PORT

redis_client = redis.Redis(host=RDF_DIFFER_REDIS_LOCATION.split('redis://')[1], port=RDF_DIFFER_REDIS_PORT)

REVOKING_QUEUE = 'revoke'


def push_task_to_revoking_queue(task_id: str, revoking_queue: str = REVOKING_QUEUE, client: redis.Redis = None):
    """
    used for adding a task's id to a queue to be "undone" or cancelled.

    :param task_id: celery task id
    :param revoking_queue: depending on the type of action you take use different queue
    :param client: redis client
    """
    client = client if client else redis_client
    client.lpush(revoking_queue, task_id)


def remove_task_from_revoking_queue(task_id: str, revoking_queue: str = REVOKING_QUEUE,
                                    client: redis.Redis = None) -> bool:
    """
    "cancel the cancellation" of a task from the specified queue

    :param task_id: celery task id
    :param revoking_queue: depending on the type of action you take use different queue
    :param client: redis client
    :return: if item was found and removed from queue return true otherwise false
    """
    client = client if client else redis_client

    return bool(client.lrem(revoking_queue, 1, task_id))


def task_exists_in_revoking_queue(task_id: str, revoking_queue: str = REVOKING_QUEUE,
                                  client: redis.Redis = None) -> bool:
    """
    check if task is in specified queue
    :param task_id: celery task id
    :param revoking_queue: depending on the type of action you take use different queue
    :param client: redis client
    :return: if item was found return true otherwise false
    """
    client = client if client else redis_client

    queue_list = client.lrange(revoking_queue, 0, -1)

    for item in queue_list:
        if item.decode() == task_id:
            return True

    return False
