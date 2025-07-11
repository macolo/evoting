from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django import forms
from .models import VotingEvent, Vote, Member, Submission, VotingReport, VotingEventInvitation
import json


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'membership_weight']
    list_filter = ['membership_weight']
    search_fields = ['name', 'email']
    ordering = ['name']


@admin.register(VotingEvent)
class VotingEventAdmin(admin.ModelAdmin):
    list_display = ['title', 'state', 'created_at', 'member_count', 'vote_count', 'submission_count']
    list_filter = ['state', 'created_at']
    search_fields = ['title']
    filter_horizontal = ['members']
    readonly_fields = ['created_at', 'updated_at', 'existing_reports_display']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'state')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
        ('Members', {
            'fields': ('members',)
        }),
        ('Reports', {
            'fields': ('existing_reports_display',),
        }),
    )
    
    def member_count(self, obj):
        """
        Display the number of members associated with a voting event in the admin list view.
        This method counts all members linked to the voting event through the many-to-many relationship.
        """
        return obj.members.count()
    member_count.short_description = 'Members'
    
    def vote_count(self, obj):
        """
        Display the number of votes (questions) configured for a voting event in the admin list view.
        This counts all Vote objects that belong to this voting event, representing the different questions or items to vote on.
        """
        return obj.votes.count()
    vote_count.short_description = 'Votes'
    
    def submission_count(self, obj):
        """
        Display the number of member submissions received for a voting event in the admin list view.
        This counts all completed voting submissions from members, indicating how many people have actually voted.
        """
        return obj.submissions.count()
    submission_count.short_description = 'Submissions'
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        Override the default change view to add custom context for conditional button display.
        This method determines which custom action buttons should be shown based on the voting event's state and data.
        It shows the invite button only when the event is closed and has members, and the generate report button only when submissions exist.
        """
        extra_context = extra_context or {}
        voting_event = get_object_or_404(VotingEvent, pk=object_id)
        
        # Add custom buttons context
        extra_context['show_invite_button'] = voting_event.state == 'closed' and voting_event.members.exists()
        extra_context['show_generate_report_button'] = voting_event.submissions.exists()
        
        return super().change_view(request, object_id, form_url, extra_context)
    
    def response_change(self, request, obj):
        """
        Handle custom form submissions from the voting event admin page.
        This method intercepts POST requests to check for custom button actions (invite members or generate report)
        and routes them to the appropriate handler methods, otherwise falls back to default Django admin behavior.
        """
        if "_invite_members" in request.POST:
            return self.invite_members(request, obj)
        elif "_generate_report" in request.POST:
            return self.generate_report(request, obj)
        return super().response_change(request, obj)
    
    def invite_members(self, request, voting_event):
        """
        Create voting invitations for all members and open the voting event.
        This method generates unique invitation tokens for each member associated with the voting event,
        changes the event state to 'open', and provides feedback on how many new invitations were created.
        Future enhancement will include sending invitation emails via Brevo API.
        """
        # Create invitations for all members
        created_count = 0
        for member in voting_event.members.all():
            invitation, created = VotingEventInvitation.objects.get_or_create(
                voting_event=voting_event,
                member=member
            )
            if created:
                created_count += 1
        
        # TODO: Implement Brevo email sending logic
        voting_event.state = 'open'
        voting_event.save()
        
        messages.success(request, f'Created {created_count} new invitations. Voting event is now open.')
        return HttpResponseRedirect(request.path)
    
    def generate_report(self, request, voting_event):
        """
        Generate a comprehensive voting report for the current voting event.
        This method creates a detailed JSON report containing vote structures, all member submissions,
        and statistical summaries, then saves it as a VotingReport object and redirects to view the report.
        """
        # Generate the voting report
        report_data = self._generate_report_data(voting_event)
        
        report = VotingReport.objects.create(
            voting_event=voting_event,
            report_data=report_data
        )
        
        messages.success(request, f'Voting report generated successfully.')
        return HttpResponseRedirect(reverse('admin:ballot_votingreport_change', args=[report.pk]))
    
    
    def existing_reports_display(self, obj):
        """
        Display existing voting reports as clickable links in the admin form.
        This readonly field shows all previously generated reports for the voting event as styled buttons
        that link directly to the report detail pages, making it easy to access historical voting data.
        """
        if not obj.pk:
            return "No reports available for new voting events."
        
        reports = obj.reports.all()
        if not reports:
            return "No reports generated yet."
        
        html_parts = []
        for report in reports:
            url = reverse('admin:ballot_votingreport_change', args=[report.pk])
            html_parts.append(
                f'<p><a href="{url}" class="button">View Report - {report.created_at.strftime("%Y-%m-%d %H:%M")}</a></p>'
            )
        
        return format_html(''.join(html_parts))
    existing_reports_display.short_description = 'Existing Reports'
    
    def _generate_report_data(self, voting_event):
        """
        Generate comprehensive JSON report data structure for a voting event.
        This private method creates a detailed report containing vote configurations, all member submissions,
        and statistical summaries including both raw counts and weighted results based on membership weights.
        The report structure includes vote metadata, individual responses, and aggregated statistics.
        """
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


class VoteAdminForm(forms.ModelForm):
    default_value = forms.CharField(
        max_length=500,
        required=False,
        help_text="Default value for short text input fields"
    )
    
    class Meta:
        model = Vote
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate default_value field from type_specific_data if it exists
        if self.instance and self.instance.pk and self.instance.type_specific_data:
            self.fields['default_value'].initial = self.instance.type_specific_data.get('default_value', '')
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Handle default_value for short_text vote type
        if self.cleaned_data.get('vote_type') == 'short_text':
            if not instance.type_specific_data:
                instance.type_specific_data = {}
            instance.type_specific_data['default_value'] = self.cleaned_data.get('default_value', '')
        
        if commit:
            instance.save()
        return instance


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    form = VoteAdminForm
    list_display = ['title', 'voting_event', 'vote_type']
    list_filter = ['vote_type', 'voting_event']
    search_fields = ['title', 'description']
    readonly_fields = ['type_specific_data']
    
    fieldsets = (
        (None, {
            'fields': ('voting_event', 'title', 'description', 'vote_type', 'default_value', 'type_specific_data')
        }),
    )
    
    class Media:
        js = ('admin/js/vote_admin.js',)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ['member', 'voting_event', 'created_at']
    list_filter = ['voting_event', 'created_at']
    search_fields = ['member__name', 'member__email', 'voting_event__title']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        """
        Prevent manual creation of submissions through the admin interface.
        Submissions should only be created through the public voting interface to ensure proper validation,
        token verification, and business logic enforcement.
        """
        return False  # Submissions are created through the voting interface


@admin.register(VotingEventInvitation)
class VotingEventInvitationAdmin(admin.ModelAdmin):
    list_display = ['member', 'voting_event', 'created_at', 'used_at', 'is_used']
    list_filter = ['voting_event', 'created_at', 'used_at']
    search_fields = ['member__name', 'member__email', 'voting_event__title', 'secret']
    readonly_fields = ['secret', 'created_at', 'used_at', 'voting_link']
    
    fieldsets = (
        (None, {
            'fields': ('voting_event', 'member')
        }),
        ('Token Information', {
            'fields': ('secret', 'voting_link'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'used_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_used(self, obj):
        """
        Display whether a voting invitation has been used in the admin list view.
        This method checks if the invitation has a 'used_at' timestamp, indicating that the member
        has successfully submitted their vote using this invitation token.
        """
        return obj.used_at is not None
    is_used.boolean = True
    is_used.short_description = 'Used'
    
    def voting_link(self, obj):
        """
        Generate and display the voting URL for an invitation in the admin interface.
        This method creates a clickable link using the invitation's secret token that opens
        the voting form in a new tab, allowing administrators to easily access and test voting links.
        """
        if obj.secret:
            from django.urls import reverse
            url = reverse('ballot:vote', args=[obj.secret])
            return format_html('<a href="{}" target="_blank">{}</a>', url, url)
        return "No link available"
    voting_link.short_description = 'Voting Link'


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
        """
        Display the JSON report data in a readable, formatted way in the admin interface.
        This method takes the raw JSON report data and formats it with proper indentation
        and syntax highlighting within a preformatted text block for easy reading and analysis.
        """
        if obj.report_data:
            return format_html('<pre>{}</pre>', json.dumps(obj.report_data, indent=2))
        return "No data"
    formatted_report_data.short_description = 'Report Data (Formatted)'
    
    def has_add_permission(self, request):
        """
        Prevent manual creation of voting reports through the admin interface.
        Reports should only be generated through the VotingEvent admin using the 'Generate Report' button
        to ensure proper data collection, formatting, and consistency.
        """
        return False  # Reports are generated through VotingEvent admin
