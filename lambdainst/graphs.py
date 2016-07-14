from datetime import timedelta, date

import pygal

from .models import User
from payments.models import BACKENDS
from payments.models import Payment


PERIOD_VERBOSE_NAME = {
    'y': "per month",
    'm': "per day",
}


def monthdelta(date, delta):
    m = (date.month + delta) % 12
    y = date.year + (date.month + delta - 1) // 12
    if not m:
        m = 12
    d = min(date.day, [31, 29 if y % 4 == 0 and not y % 400 == 0
                       else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31
                       ][m - 1])
    return date.replace(day=d, month=m, year=y)


def last_days(n=30):
    now = date.today()
    for i in range(n - 1, -1, -1):
        yield now - timedelta(days=i)


def last_months(n=12):
    now = date.today().replace(day=1)
    for i in range(n - 1, -1, -1):
        yield monthdelta(now, -i)


def time_filter_future(period, m, df):
    def _filter(o):
        if period == 'm':
            return df(o).date() <= m
        if period == 'y':
            return df(o).date().replace(day=1) <= m
    return _filter


def time_filter_between(period, m, df):
    def _filter(o):
        if period == 'm':
            return df(o).year == m.year and df(o).month == m.month and df(o).day == m.day
            return df(o).date() <= m and df(o).date() > (m - timedelta(days=1))
        if period == 'y':
            return df(o).year == m.year and df(o).month == m.month
            return (df(o).date().replace(day=1) <= m and
                    df(o).date().replace(day=1) > (m - timedelta(days=30)))
    return _filter


def users_graph(period):
    chart = pygal.Line(fill=True, x_label_rotation=75, show_legend=False)
    chart.title = 'Users %s' % PERIOD_VERBOSE_NAME[period]
    chart.x_labels = []
    values = []
    gen = last_days(30) if period == 'm' else last_months(12)
    users = User.objects.all()

    for m in gen:
        filter_ = time_filter_future(period, m, lambda o: o.date_joined)
        users_filtered = filter(filter_, users)
        values.append(len(list(users_filtered)))
        chart.x_labels.append('%02d/%02d' % (m.month, m.day))

    chart.add('Users', values)
    return chart.render()


def payments_paid_graph(period):
    chart = pygal.StackedBar(x_label_rotation=75, show_legend=True)
    chart.x_labels = []
    gen = list(last_days(30) if period == 'm' else last_months(12))

    chart.title = 'Payments %s in €' % (PERIOD_VERBOSE_NAME[period])

    for m in gen:
        chart.x_labels.append('%02d/%02d' % (m.month, m.day))

    values = dict()
    for backend_id, backend in BACKENDS.items():
        values = []
        payments = list(Payment.objects.filter(status='confirmed', backend_id=backend_id))

        for m in gen:
            filter_ = time_filter_between(period, m, lambda o: o.created)
            filtered = filter(filter_, payments)
            values.append(sum(u.paid_amount for u in filtered) / 100)

        chart.add(backend_id, values)

    return chart.render()


def payments_success_graph(period):
    chart = pygal.StackedBar(x_label_rotation=75, show_legend=True)
    chart.x_labels = []
    gen = list(last_days(30) if period == 'm' else last_months(12))

    chart.title = 'Successful payments %s' % (PERIOD_VERBOSE_NAME[period])

    for m in gen:
        chart.x_labels.append('%02d/%02d' % (m.month, m.day))

    values = dict()
    for backend_id, backend in BACKENDS.items():
        values = []
        payments = list(Payment.objects.filter(status='confirmed', backend_id=backend_id))

        for m in gen:
            filter_ = time_filter_between(period, m, lambda o: o.created)
            filtered = filter(filter_, payments)
            values.append(sum(1 for u in filtered))

        chart.add(backend_id, values)

    return chart.render()

