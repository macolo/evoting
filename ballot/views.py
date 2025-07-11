from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.utils.crypto import get_random_string
from .models import VotingEvent, Member, Submission, Vote
import json


def vote_view(request, token):
    """Display the voting form for a member with a valid token"""
    # Decode the token to get voting event and member
    voting_event_id, member_id = VotingEvent.decode_token(token)
    
    if not voting_event_id or not member_id:
        return HttpResponse("Invalid token", status=400)
    
    # Get the voting event and member
    voting_event = get_object_or_404(VotingEvent, pk=voting_event_id)
    member = get_object_or_404(Member, pk=member_id)
    
    # Check if voting event is open
    if voting_event.state != 'open':
        return redirect('ballot:vote_closed')
    
    # Check if member is authorized for this voting event
    if not voting_event.members.filter(pk=member.id).exists():
        return HttpResponse("You are not authorized to vote in this event", status=403)
    
    # Check if member has already voted
    if Submission.objects.filter(voting_event=voting_event, member=member).exists():
        return redirect('ballot:already_voted')
    
    # Get all votes for this voting event
    votes = voting_event.votes.all()
    
    context = {
        'voting_event': voting_event,
        'member': member,
        'votes': votes,
        'token': token,
    }
    
    return render(request, 'ballot/vote_form.html', context)


def submit_vote(request, token):
    """Handle vote submission"""
    if request.method != 'POST':
        return redirect('ballot:vote', token=token)
    
    # Decode the token to get voting event and member
    voting_event_id, member_id = VotingEvent.decode_token(token)
    
    if not voting_event_id or not member_id:
        return HttpResponse("Invalid token", status=400)
    
    # Get the voting event and member
    voting_event = get_object_or_404(VotingEvent, pk=voting_event_id)
    member = get_object_or_404(Member, pk=member_id)
    
    # Check if voting event is open
    if voting_event.state != 'open':
        return redirect('ballot:vote_closed')
    
    # Check if member is authorized for this voting event
    if not voting_event.members.filter(pk=member.id).exists():
        return HttpResponse("You are not authorized to vote in this event", status=403)
    
    # Check if member has already voted
    if Submission.objects.filter(voting_event=voting_event, member=member).exists():
        return redirect('ballot:already_voted')
    
    # Collect submission data from form
    submission_data = {}
    votes = voting_event.votes.all()
    
    for vote in votes:
        field_name = f'vote_{vote.id}'
        if field_name in request.POST:
            submission_data[str(vote.id)] = request.POST[field_name]
    
    # Create the submission
    Submission.objects.create(
        voting_event=voting_event,
        member=member,
        submission_data=submission_data
    )
    
    messages.success(request, 'Your vote has been submitted successfully!')
    return redirect('ballot:vote_success', voting_event_id=voting_event.id)


def vote_closed(request):
    """Display message when voting is closed"""
    return render(request, 'ballot/vote_closed.html')


def already_voted(request):
    """Display message when member has already voted"""
    return render(request, 'ballot/already_voted.html')


def vote_success(request, voting_event_id):
    """Display success message after voting"""
    voting_event = get_object_or_404(VotingEvent, pk=voting_event_id)
    return render(request, 'ballot/vote_success.html', {'voting_event': voting_event})
