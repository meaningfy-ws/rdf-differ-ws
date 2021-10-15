import redis

from rdf_differ.config import RDF_DIFFER_REDIS_LOCATION, RDF_DIFFER_REDIS_PORT

redis_client = redis.Redis(host=RDF_DIFFER_REDIS_LOCATION, port=RDF_DIFFER_REDIS_PORT)

REVOKING_QUEUE = 'revoke'


def push_task_to_revoking_queue(task_id: str, revoking_queue: str = REVOKING_QUEUE, client: redis.Redis = None):
    client = client if client else redis_client
    client.lpush(revoking_queue, task_id)


def remove_task_from_revoking_queue(task_id: str, revoking_queue: str = REVOKING_QUEUE,
                                    client: redis.Redis = None) -> bool:
    client = client if client else redis_client

    return bool(client.lrem(revoking_queue, 1, task_id))


def task_exists_in_revoking_queue(task_id: str, revoking_queue: str = REVOKING_QUEUE,
                                  client: redis.Redis = None) -> bool:
    client = client if client else redis_client

    queue_list = client.lrange(revoking_queue, 0, -1)

    for item in queue_list:
        if item.decode() == task_id:
            return True

    return False
