from datetime import timedelta
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .forms import NewPaymentForm
from .models import Payment, BACKENDS


monthly_price = settings.PAYMENTS_MONTHLY_PRICE


@login_required
def new(request):
    if request.method != 'POST':
        return redirect('account:index')

    form = NewPaymentForm(request.POST)

    if not form.is_valid():
        return redirect('account:index')

    months = int(form.cleaned_data['time'])
    payment = Payment(
        user=request.user,
        backend_id=form.cleaned_data['method'],
        status='new',
        time=timedelta(days=30 * months),
        amount=monthly_price * months
    )

    if not payment.backend.backend_enabled:
        return HttpResponseNotFound()

    payment.save()

    r = payment.backend.new_payment(payment)

    if not r:
        payment.status = 'error'
        payment.save()
        raise Exception("Failed to initialize payment #%d" % payment.id)

    if isinstance(r, str):
        return render(request, 'payments/form.html', dict(html=r))
    elif r is None:
        return redirect('payments:view', payment.id)

    return r


@csrf_exempt
def callback_paypal(request, id):
    """ PayPal IPN """
    if not BACKENDS['paypal'].backend_enabled:
        return HttpResponseNotFound()

    p = Payment.objects.get(id=id)
    if BACKENDS['paypal'].callback(p, request):
        return HttpResponse()
    else:
        return HttpResponseBadRequest()


@csrf_exempt
@login_required
def callback_stripe(request, id):
    """ Stripe button POST """
    if not BACKENDS['stripe'].backend_enabled:
        return HttpResponseNotFound()

    p = Payment.objects.get(id=id)
    BACKENDS['stripe'].callback(p, request)
    return redirect(reverse('payments:view', args=(id,)))


@csrf_exempt
def callback_coinbase(request):
    if not BACKENDS['coinbase'].backend_enabled:
        return HttpResponseNotFound()

    if BACKENDS['coinbase'].callback(Payment, request):
        return HttpResponse()
    else:
        return HttpResponseBadRequest()


@login_required
@csrf_exempt
def view(request, id):
    p = Payment.objects.get(id=id, user=request.user)
    return render(request, 'payments/view.html', dict(payment=p))


@login_required
def cancel(request, id):
    p = Payment.objects.get(id=id, user=request.user)
    if p.status == 'new':
        p.status = 'cancelled'
        p.save()
    return render(request, 'payments/view.html', dict(payment=p))


@login_required
def list_payments(request):
    # Only show recent cancelled payments
    cancelled_limit = timezone.now() - timedelta(days=3)

    objects = request.user.payment_set.exclude(status='cancelled',
                                               created__lte=cancelled_limit)
    return render(request, 'payments/list.html', dict(payments=objects))

