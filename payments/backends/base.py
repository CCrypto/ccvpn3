from django.utils.translation import ugettext_lazy as _


class BackendBase:
    backend_id = None
    backend_verbose_name = ""
    backend_display_name = ""
    backend_enabled = False
    backend_has_recurring = False

    def __init__(self, settings):
        pass

    def new_payment(self, payment):
        """ Initialize a payment and returns an URL to redirect the user.
        Can return a HTML string that will be sent back to the user in a
        default template (like a form) or a HTTP response (like a redirect).
        """
        raise NotImplementedError()

    def callback(self, payment, request):
        """ Handle a callback """
        raise NotImplementedError()

    def callback_subscr(self, payment, request):
        """ Handle a callback (recurring payments) """
        raise NotImplementedError()

    def cancel_subscription(self, subscr):
        """ Cancel a subscription """
        raise NotImplementedError()

    def get_info(self):
        """ Returns some status (key, value) list """
        return ()

    def get_ext_url(self, payment):
        """ Returns URL to external payment view, or None """
        return None

    def get_subscr_ext_url(self, subscr):
        """ Returns URL to external payment view, or None """
        return None


class ManualBackend(BackendBase):
    """ Manual backend used to store and display informations about a
    payment processed manually.
    More a placeholder than an actual payment beckend, everything raises
    NotImplementedError().
    """

    backend_id = 'manual'
    backend_verbose_name = _("Manual")


