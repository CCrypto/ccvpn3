from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http.response import HttpResponseNotFound
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.translation import ugettext as _

from ccvpn.common import get_client_ip
from .models import Ticket, TicketMessage
from .forms import NewTicketForm, ReplyForm, StaffReplyForm


def common_context(request):
    context = {
        'open_n': Ticket.objects.filter(is_open=True, user=request.user).count(),
        'closed_n': Ticket.objects.filter(is_open=False, user=request.user).count(),
    }
    if request.user.has_perm('tickets.view_any_ticket'):
        context.update({
            'all_open_n': Ticket.objects.filter(is_open=True).count(),
            'all_closed_n': Ticket.objects.filter(is_open=False).count(),
        })
    return context


@login_required
def index(request, f=None, all=False):
    tickets = Ticket.objects

    if f == 'closed':
        tickets = tickets.filter(is_open=False)
    else:
        tickets = tickets.filter(is_open=True)

    if all is False or not request.user.has_perm('tickets.view_any_ticket'):
        tickets = tickets.filter(user=request.user)
        single_user = True
    else:
        single_user = False

    paginator = Paginator(tickets, 20)
    page = request.GET.get('page')
    try:
        tickets = paginator.page(page)
    except PageNotAnInteger:
        tickets = paginator.page(1)
    except EmptyPage:
        tickets = paginator.page(paginator.num_pages)

    context = dict(
        tickets=tickets,
        filter=f,
        single_user=single_user,
        title=_("Tickets"),
    )
    context.update(common_context(request))
    if not f:
        return render(request, 'tickets/index.html', context)
    else:
        return render(request, 'tickets/list.html', context)


@login_required
def new(request):
    context = common_context(request)
    context['title'] = _("New Ticket")
    if request.method != 'POST':
        context['form'] = NewTicketForm()
        return render(request, 'tickets/new.html', context)

    form = NewTicketForm(request.POST)

    if not form.is_valid():
        context['form'] = form
        return render(request, 'tickets/new.html', context)

    ticket = Ticket(category=form.cleaned_data['category'],
                    subject=form.cleaned_data['subject'],
                    user=request.user)
    ticket.save()

    firstmsg = TicketMessage(ticket=ticket, user=request.user,
                             message=form.cleaned_data['message'])

    if not request.user.is_staff:
        firstmsg.remote_addr = get_client_ip(request)

    firstmsg.save()

    ticket.notify_new(firstmsg)

    return redirect('tickets:view', id=ticket.id)


@login_required
def view(request, id):
    ticket = get_object_or_404(Ticket, id=id)

    view_any_ticket = request.user.has_perm('tickets.view_any_ticket')
    reply_any_ticket = request.user.has_perm('tickets.reply_any_ticket')

    if not view_any_ticket and ticket.user != request.user:
        return HttpResponseNotFound()

    if request.user.has_perm('tickets.view_private_message'):
        messages = ticket.message_set.all()
    else:
        messages = ticket.message_set.filter(staff_only=False)

    if request.method != 'POST':
        ctx = dict(
            staff_reply=request.user.has_perm('tickets.post_private_message'),
            ticket=ticket,
            ticket_messages=messages,
            form=ReplyForm(),
            title=_("Ticket:") + " " + ticket.subject,
        )
        ctx.update(common_context(request))
        return render(request, 'tickets/view.html', ctx)

    if not reply_any_ticket and ticket.user != request.user:
        return HttpResponseNotFound()

    if request.POST.get('close') or request.POST.get('button_close'):
        ticket.is_open = False
        ticket.closed = timezone.now()
        ticket.save()
        return redirect('tickets:view', id=ticket.id)

    if request.POST.get('reopen') or request.POST.get('button_reopen'):
        ticket.is_open = True
        ticket.save()
        return redirect('tickets:view', id=ticket.id)

    if request.user.has_perm('tickets.post_private_message'):
        form = StaffReplyForm(request.POST)
    else:
        form = ReplyForm(request.POST)

    if not form.is_valid():
        ctx = dict(
            staff_reply=request.user.has_perm('tickets.post_private_message'),
            ticket=ticket,
            ticket_messages=messages,
            form=form,
            title=_("Ticket:") + " " + ticket.subject,
        )
        ctx.update(common_context(request))
        return render(request, 'tickets/view.html', ctx)

    msg = TicketMessage(ticket=ticket, user=request.user,
                        **form.cleaned_data)

    if not request.user.is_staff:
        msg.remote_addr = get_client_ip(request)

    msg.save()

    if not ticket.is_open:
        ticket.is_open = True
        ticket.save()

    ticket.notify_reply(msg)

    return redirect('tickets:view', id=ticket.id)



