import redis


class Store:
    def __init__(self, host='localhost', port=6379, retries=3, timeout=3):
        self.retries = retries
        self.timeout = timeout
        self.host = host
        self.port = port
        self.connect()

    def connect(self):
        self.redis = redis.Redis(
            db=0,
            connection_pool=None,
            host=self.host,
            port=self.port,
            socket_connect_timeout=self.timeout,
            socket_timeout=self.timeout
        )

    def set(self, key, value, timeout):
        return self.redis.set(key, value, ex=timeout)

    def get(self, key):
        retries = 0
        while retries <= self.retries:
            try:
                value = self.redis.get(key)
                return value.decode("utf-8")
            except redis.exceptions.ConnectionError:
                self.connect()
                retries += 1
            except (AttributeError, ValueError):
                return
        raise redis.exceptions.ConnectionError

    def cache_get(self, key):
        try:
            return self.get(key=key)
        except redis.exceptions.ConnectionError:
            return None

    def cache_set(self, key, value, timeout):
        self.set(key, value, timeout)
