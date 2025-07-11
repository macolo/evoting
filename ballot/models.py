from django.db import models
from django.core.validators import MinValueValidator
import json


class Member(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    membership_weight = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    class Meta:
        ordering = ['name']


class VotingEvent(models.Model):
    STATE_CHOICES = [
        ('closed', 'Closed'),
        ('open', 'Open'),
    ]
    
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    state = models.CharField(max_length=10, choices=STATE_CHOICES, default='closed')
    members = models.ManyToManyField(Member, related_name='voting_events', blank=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']


class Vote(models.Model):
    VOTE_TYPES = [
        ('simple', 'Simple Vote (Agree/Disagree/Abstain)'),
        ('short_text', 'Short Text Input'),
        ('radio', 'Radio Buttons'),
    ]
    
    voting_event = models.ForeignKey(VotingEvent, on_delete=models.CASCADE, related_name='votes')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    vote_type = models.CharField(max_length=20, choices=VOTE_TYPES)
    type_specific_data = models.JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_vote_type_display()})"
    
    class Meta:
        ordering = ['id']


class Submission(models.Model):
    voting_event = models.ForeignKey(VotingEvent, on_delete=models.CASCADE, related_name='submissions')
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='submissions')
    submission_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.member.name} - {self.voting_event.title}"
    
    class Meta:
        unique_together = ['voting_event', 'member']
        ordering = ['-created_at']


class VotingReport(models.Model):
    voting_event = models.ForeignKey(VotingEvent, on_delete=models.CASCADE, related_name='reports')
    report_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Report for {self.voting_event.title} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-created_at']
