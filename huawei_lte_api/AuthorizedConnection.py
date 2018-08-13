import datetime
from huawei_lte_api.Connection import Connection
from huawei_lte_api.ApiGroup import ApiGroup
from huawei_lte_api.api.User import User


def authorized_call(fn):
    def wrapped(*args, **kw):
        # First argument should be self of class
        if not isinstance(args[0], ApiGroup):
            raise Exception('{} is not instance of ApiGroup'.format(args[0]))

        if not isinstance(args[0]._connection, AuthorizedConnection):
            raise Exception('{} is not instance of AuthorizedConnection needed by {}'.format(args[0]._connection, fn))

        if not args[0]._connection.enforce_authorized_connection():
            raise Exception('{}: Failed to enforce login for  {}'.format(args[0]._connection, fn))

        return fn(*args, **kw)
    return wrapped


class AuthorizedConnection(Connection):
    LOGOUT_TIMEOUT = 300  # seconds
    login_time = None
    logged_in = False

    def __init__(self, url: str, username: str, password: str):
        super(AuthorizedConnection, self).__init__(url)
        self.user = User(self)
        if self.user.login(username, password):
            self.login_time = datetime.datetime.utcnow()
            self.logged_in = True

    def _is_login_timeout(self) -> bool:
        if self.login_time is None:
            return True
        logout_time = self.login_time + datetime.timedelta(seconds=self.LOGOUT_TIMEOUT)
        return logout_time < datetime.datetime.utcnow()

    def enforce_authorized_connection(self):
        # Check if connection timeouted or not
        if not self.logged_in or self._is_login_timeout():
            # Connection timeouted, relogin
            if self.user._enforce_logged():
                self.login_time = datetime.datetime.utcnow()
                self.logged_in = True
            else:
                self.login_time = None
                self.logged_in = False

        return self.logged_in
