from amqplib import client_0_8 as amqp


class BaseAMQPConnection(object):
    virtual_host = "/"
    port = 5672
    insist = False

    def __init__(self, hostname, userid, password,
            virtual_host=None, port=None, **kwargs):
        self.hostname = hostname
        self.userid = userid
        self.password = password
        self.virtual_host = virtual_host or self.virtual_host
        self.port = port or self.port
        self.insist = kwargs.get("insist", self.insist)

        self.connect()

    def connect(self):
        self.connection = amqp.Connection(host=self.host,
                                          userid=self.userid,
                                          password=self.password,
                                          virtual_host=self.virtual_host,
                                          insist=self.insist)

    def close(self):
        if getattr(self, "connection"):
            self.connection.close()

    def __del__(self):
        self.close()

    @property
    def host(self):
        return ":".join([self.hostname, str(self.port)])


class AMQPConnection(BaseAMQPConnection):

    def __init__(self, *args, **kwargs):
        kwargs = SettingsProvider(kwargs).get_settings()
        super(AMQPConnection, self).__init__(*args, **kwargs)


class SettingsProvider(object):
    """
    Provides conditional lookup of settings from passed arguments,
    django settings or the current environment.

    Falls from passed arguments to django (if present) to environment vars.
    """

    setting_env_map = {
        'hostname': 'AMQP_SERVER',
        'userid': 'AMQP_USER',
        'password': 'AMQP_PASSWORD',
        'virtual_host': 'AMQP_VHOST',
        'port': 'AMQP_PORT',
    }

    def __init__(self, provided_settings):
        self.provided_settings = provided_settings or {}
        self.lookups = (
            self._django_lookup,
            self._env_lookup,
        )

    def _django_lookup(self, name, default):
        try:
            from django.conf import settings
            return getattr(settings, name, default)
        except:
            return default

    def _env_lookup(self, name, default):
        from os import environ
        return environ.get(name, default)

    def lookup(self, name, default=None):
        result = default
        for lookup_method in self.lookups:
            if result == default:
                result = lookup_method(name, default)
        return result

    def get_settings(self):
        settings = {}
        for name, env_var in self.setting_env_map.items():
            settings[name] = self.lookup(env_var)
        settings.update(self.provided_settings)
        return settings
