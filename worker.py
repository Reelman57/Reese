# worker.py
import os
import redis
from rq import Worker, Queue, Connection

from app import send_emails, send_voice

listen = ['high', 'default', 'low']
redis_url = os.getenv('REDISCLOUD_URL', os.getenv('REDIS_URL', 'redis://localhost:6379'))
conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
