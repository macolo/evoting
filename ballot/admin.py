from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import get_object_or_404
from .models import VotingEvent, Vote, Member, Submission, VotingReport
import json


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'membership_weight']
    list_filter = ['membership_weight']
    search_fields = ['name', 'email']
    ordering = ['name']


class VoteInline(admin.TabularInline):
    model = Vote
    extra = 0
    fields = ['title', 'description', 'vote_type', 'type_specific_data']
    readonly_fields = []


@admin.register(VotingEvent)
class VotingEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'state', 'created_at', 'member_count', 'vote_count', 'submission_count']
    list_filter = ['state', 'created_at']
    search_fields = ['title']
    filter_horizontal = ['members']
    inlines = [VoteInline]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'state')
        }),
        ('Members', {
            'fields': ('members',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def member_count(self, obj):
        return obj.members.count()
    member_count.short_description = 'Members'
    
    def vote_count(self, obj):
        return obj.votes.count()
    vote_count.short_description = 'Votes'
    
    def submission_count(self, obj):
        return obj.submissions.count()
    submission_count.short_description = 'Submissions'
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        voting_event = get_object_or_404(VotingEvent, pk=object_id)
        
        # Add custom buttons context
        extra_context['show_invite_button'] = voting_event.state == 'closed' and voting_event.members.exists()
        extra_context['show_generate_report_button'] = voting_event.submissions.exists()
        extra_context['existing_reports'] = voting_event.reports.all()
        
        return super().change_view(request, object_id, form_url, extra_context)
    
    def response_change(self, request, obj):
        if "_invite_members" in request.POST:
            return self.invite_members(request, obj)
        elif "_generate_report" in request.POST:
            return self.generate_report(request, obj)
        return super().response_change(request, obj)
    
    def invite_members(self, request, voting_event):
        # TODO: Implement Brevo email sending logic
        voting_event.state = 'open'
        voting_event.save()
        messages.success(request, f'Invitations sent to {voting_event.members.count()} members. Voting event is now open.')
        return HttpResponseRedirect(request.path)
    
    def generate_report(self, request, voting_event):
        # Generate the voting report
        report_data = self._generate_report_data(voting_event)
        
        report = VotingReport.objects.create(
            voting_event=voting_event,
            report_data=report_data
        )
        
        messages.success(request, f'Voting report generated successfully.')
        return HttpResponseRedirect(reverse('admin:ballot_votingreport_change', args=[report.pk]))
    
    def _generate_report_data(self, voting_event):
        """Generate the JSON report data structure"""
        report = {
            "Id": str(voting_event.id),
            "voting_event_id": str(voting_event.id),
            "title": voting_event.title,
            "votes": [],
            "submissions": [],
            "summary": {}
        }
        
        # Add votes structure
        for vote in voting_event.votes.all():
            vote_data = {
                "id": str(vote.id),
                "type": vote.vote_type,
                "title": vote.title,
                "description": vote.description,
            }
            
            if vote.vote_type == 'simple':
                vote_data["options"] = [
                    {"id": "agree", "label": "Agree"},
                    {"id": "disagree", "label": "Disagree"},
                    {"id": "abstain", "label": "Abstain"}
                ]
            elif vote.vote_type == 'short_text':
                vote_data["default_value"] = vote.type_specific_data.get('default_value', '')
            elif vote.vote_type == 'radio':
                vote_data["options"] = vote.type_specific_data.get('options', [])
            
            report["votes"].append(vote_data)
        
        # Add submissions and calculate summary
        vote_summaries = {}
        
        for submission in voting_event.submissions.all():
            submission_data = {
                "member_id": submission.member.id,
                "member_email": submission.member.email,
                "weight": submission.member.membership_weight,
                "votes": submission.submission_data
            }
            report["submissions"].append(submission_data)
            
            # Calculate summary
            for vote_key, vote_value in submission.submission_data.items():
                if vote_key not in vote_summaries:
                    vote_summaries[vote_key] = {"count": {}, "weighted": {}}
                
                # Count occurrences
                if vote_value not in vote_summaries[vote_key]["count"]:
                    vote_summaries[vote_key]["count"][vote_value] = 0
                    vote_summaries[vote_key]["weighted"][vote_value] = 0
                
                vote_summaries[vote_key]["count"][vote_value] += 1
                vote_summaries[vote_key]["weighted"][vote_value] += submission.member.membership_weight
        
        report["summary"] = vote_summaries
        return report


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'voting_event', 'vote_type']
    list_filter = ['vote_type', 'voting_event']
    search_fields = ['title', 'description']
    
    fieldsets = (
        (None, {
            'fields': ('voting_event', 'title', 'description', 'vote_type')
        }),
        ('Type-specific Configuration', {
            'fields': ('type_specific_data',),
            'description': 'JSON configuration for vote type (e.g., radio button options, default values)'
        }),
    )


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['member', 'voting_event', 'created_at']
    list_filter = ['voting_event', 'created_at']
    search_fields = ['member__name', 'member__email', 'voting_event__title']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # Submissions are created through the voting interface


@admin.register(VotingReport)
class VotingReportAdmin(admin.ModelAdmin):
    list_display = ['voting_event', 'created_at']
    list_filter = ['voting_event', 'created_at']
    readonly_fields = ['created_at', 'formatted_report_data']
    
    fieldsets = (
        (None, {
            'fields': ('voting_event', 'created_at')
        }),
        ('Report Data', {
            'fields': ('formatted_report_data',),
            'classes': ('collapse',)
        }),
    )
    
    def formatted_report_data(self, obj):
        if obj.report_data:
            return format_html('<pre>{}</pre>', json.dumps(obj.report_data, indent=2))
        return "No data"
    formatted_report_data.short_description = 'Report Data (Formatted)'
    
    def has_add_permission(self, request):
        return False  # Reports are generated through VotingEvent admin
