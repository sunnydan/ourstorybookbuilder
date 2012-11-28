import random
from fuzzywuzzy import fuzz, process
from django.template.loader import get_template
from recaptcha.client import captcha
from django.template import Context
from django.template import RequestContext
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from ourstorybook.adventure.models import Branch
from django.http import HttpResponseRedirect
from forms import BranchForm
from helpers import *
from fields import ReCaptchaField


def learnmore(request):
    return render_to_response("learnmore.html",
                              context_instance=RequestContext(request))


def landing_page(request):
    return render_to_response("base.html",
                              context_instance=RequestContext(request))


# Turn the form request data into the url of a branch.
def convert_request_to_url(request):
    if 'current' in request.GET:
        current = request.GET['current']
        acty = request.GET['acty']
        return HttpResponseRedirect('/branch/' + current + '-' + acty + '/')
    if 'parent_id' in request.GET:
        parent_id = request.GET['parent_id']
        action = request.GET['action']
        return HttpResponseRedirect('/edit/' + parent_id + '-' + action + '/')
    if 'search' in request.GET:
        search = request.GET['search']
        return HttpResponseRedirect('/search/' + search + '/')
    else:
        return goHome()


def serve_branch_by_id(request, idy):
    branch = Branch.objects.all().get(id=idy)
    if branch.id == 1:
        return HttpResponseRedirect('/branch/-/')
    return HttpResponseRedirect('/branch/' + str(branch.parent.id) +
                                '-' + branch.action + '/')


def serve_branch(request, parent_id, action):
    # Get branch matching parent_id and action.
    branch = findBranch(parent_id, action)

    # If the requested branch does not already exist...
    if branch == None:
        branches = Branch.objects.all()
        available = False
        # Check to see if a new branch would have a parent.
        for branch in branches:
            if branch.id == int(parent_id):
                available = True
        # If it would, allow the user to write a new branch.
        if available == True:
            # Give the user a writing permit for that branch.
            request.session["Permitted_Parent"] = parent_id
            request.session["Permitted_Action"] = action
            return HttpResponseRedirect('/edit/' + parent_id + '-' +
                                        action + '/')
        else:
            # If a new branch would be an orphan, go back to the landing.
            return goHome()

    # If the requested branch DOES already exist...
    else:
        # See if the user wrote it, and thus is allowed to edit it.
        mine = myBranch(request.user, branch)

    seed = False
    # If the requested branch is the Seed, the template will not allow voting.
    if branch.id == 1:
        seed = True

    # Create a short list of random branches the user could go to.
    randombranches = []
    possiblebranches = Branch.objects.all().filter(parent=branch.id)
    original_length_of_possiblebranches = len(possiblebranches)
    if possiblebranches:
        x = 0
        while x < 50 and x < original_length_of_possiblebranches:
            randombranch = possiblebranches[random.randint(0,
                                             len(possiblebranches) - 1)]
            randombranches.append(randombranch)
            possiblebranches = possiblebranches.exclude(id=randombranch.id)
            x += 1

    return render_to_response("branch.html", {'branch': branch, 'mine': mine,
                              'seed': seed, 'branches': randombranches},
                              context_instance=RequestContext(request))


def edit_branch(request, parent_id, action):
    branch = findBranch(parent_id, action)
    mine = myBranch(request.user, branch)
    allow = False
    if mine == True:
        allow = True
    else:
        # Check that user has a permit for the writing of this branch or it is
        # their branch already.
        if (parent_id == request.session["Permitted_Parent"] and
                action == request.session["Permitted_Action"]):
            allow = True
    if allow == True:
        # If the request is not submitting a branch already...
        if not request.method == "POST":
            # If the user is making a NEW BRANCH...
            if branch == None:
                # Get the aew branch writing form.
                form = BranchForm
            # If the user is EDITING an EXISTING BRANCH...
            else:
                # Get the existing text...
                already_written = {'text': branch.text}
                # And fill in the form with it by default.
                form = BranchForm(already_written)
            if not request.user.is_authenticated():
                # And make note that this will be the first attempt at
                # submitting the branch.
                request.session["resubmit"] = False
            return render_to_response("new.html", {'form': form,
                     'parent': Branch.objects.all().get(id=parent_id),
                     'action': action},
                     context_instance=RequestContext(request))

        # If the request IS submitting a new branch already...
        else:
            # Store what the user has made so far, so it is not lost.
            form = BranchForm(request.POST)

            error = False
            # Check to see if the user is anonymous.
            if not request.user.is_authenticated():
                # If this is the first attempt at submission...
                if request.session["resubmit"] == False:
                    # In which case, require them to resubmit.
                    error = 'Not logged in. Resubmit to submit' + \
                                    ' as anonymous user.'
                    # Make note that will be their second attempt at
                    # submission.
                    request.session["resubmit"] = True

            # If their captcha is good, they have written something, and they
            # are either logged in or resubmitting...
            if form.is_valid() and error == False:
                cd = form.cleaned_data
                # If the user is not editing an existing branch, a new one will
                # be created.
                if mine == False:
                    branch = Branch()
                    # Set the branch's ratings to default.
                    branch.entertainment = deci(10)
                    branch.writing = deci(10)
                    branch.immersiveness = deci(10)
                    branch.interest = deci(10)
                branch.action = action
                branch.text = cd['text']
                branch.parent = Branch.objects.all().get(id=parent_id)
                # If the user is logged in, make them the author.
                if request.user.is_authenticated():
                    branch.author = request.user
                else:
                    # Otherwise, make the author anonymous.
                    branch.author = \
                        User.objects.all().get(username="Anonymous")
                # Create the new branch! Yay!
                branch.save()
                # Give all session values a value just to make the deletion
                # clean.
                request.session["resubmit"] = None
                request.session["Permitted_Parent"] = None
                request.session["Permitted_Action"] = None
                # Put away your notepad.
                del request.session["resubmit"]
                # Take the user's writing permit.
                del request.session["Permitted_Parent"]
                del request.session["Permitted_Action"]
                # Allow the user to edit the new branch if they are logged in.
                mine = myBranch(request.user, branch)
                # Let them see their new branch.
                return HttpResponseRedirect("/branch/" +
                        str(branch.parent.id) + "-" + branch.action + "/")
            # If something is WRONG with their new branch, go back and let them
            # fix it.
            else:
                return render_to_response("new.html", {'form': form,
                         'parent': Branch.objects.all().get(id=parent_id),
                         'action': action, 'errors': error},
                         context_instance=RequestContext(request))
    # If the user does NOT have a writing permit...
    else:
        # send them to the landing.
        return goHome()


def vote_processor(request, parent_id, action):
    branch = findBranch(parent_id, action)
    mine = myBranch(request.user, branch)
    # User must be logged in to vote, but cannot vote on their own branch.
    # Cannot vote on Seed.
    if request.method == "POST" and request.user.is_authenticated() and \
                      branch != None and mine == False and branch.id != 1:
        if 'entertainment' in request.POST and not \
                     branch.already_voted(request.user, "ent"):
            vote = getUserRating(request.user) * \
                          int(request.POST['entertainment'])
            branch.entertainment = int(branch.entertainment) + int(vote)
            branch.voted_ent.add(request.user)
        if 'writing' in request.POST and not \
                          branch.already_voted(request.user, "wri"):
            vote = getUserRating(request.user) * int(request.POST['writing'])
            branch.writing = int(branch.writing) + int(vote)
            branch.voted_wri.add(request.user)
        if 'immersiveness' in request.POST and not \
                          branch.already_voted(request.user, "imm"):
            vote = getUserRating(request.user) * \
                           int(request.POST['immersiveness'])
            branch.immersiveness = int(branch.immersiveness) + int(vote)
            branch.voted_imm.add(request.user)
        if 'interest' in request.POST and not \
                          branch.already_voted(request.user, "int"):
            vote = getUserRating(request.user) * int(request.POST['interest'])
            branch.interest = int(branch.interest) + int(vote)
            branch.voted_int.add(request.user)
        branch.save()
        if branch.get_overall() < .5:
            branch.kill_branch()
            return goHome()
    else:
        return goHome()
    return HttpResponseRedirect("/branch/" + str(branch.parent.id) + "-" +
                                                 branch.action + "/")


def kill_branch(request):
    if 'parent_id' in request.GET:
        parent_id = request.GET['parent_id']
        action = request.GET['action']
        branch = findBranch(parent_id, action)
        if request.user.is_authenticated():
            mine = myBranch(request.user, branch)
            if mine == True:
                branch.kill_branch()
    return goHome()


def userpage(request):
    # If the user is logged in...
    if request.user.is_authenticated():
        # Show them the branches they have written.
        branches = Branch.objects.all().filter(author=request.user)
        # Their overall rating.
        overall = getUserRating(request.user)
        entertainment = 0
        writing = 0
        immersiveness = 0
        interest = 0
        for branch in branches:
            entertainment += branch.get_entertainment()
            writing += branch.get_writing()
            immersiveness += branch.get_immersiveness()
            interest += branch.get_interest()
        if branches:
            entertainment = entertainment / len(branches)
            writing = writing / len(branches)
            immersiveness = immersiveness / len(branches)
            interest = interest / len(branches)
        return render_to_response("userpage.html", {'branches': branches,
                  'overall': overall, 'entertainment': entertainment,
                  'writing': writing, 'immersiveness': immersiveness,
                  'interest': interest},
                  context_instance=RequestContext(request))
    else:
        return goHome()


def other_userpage(request, search_username):
    if request.user.is_authenticated():
        if request.user == search_username:
            return HttpResponseRedirect("/userpage/")
        users = User.objects.all()
        for foruser in users:
            if str(foruser) == search_username:
                branches = Branch.objects.all().filter(author=foruser)
                overall = getUserRating(foruser)
                entertainment = 0
                writing = 0
                immersiveness = 0
                interest = 0
                for branch in branches:
                    entertainment += branch.get_entertainment()
                    writing += branch.get_writing()
                    immersiveness += branch.get_immersiveness()
                    interest += branch.get_interest()
                if branches:
                    entertainment = entertainment / len(branches)
                    writing = writing / len(branches)
                    immersiveness = immersiveness / len(branches)
                    interest = interest / len(branches)
                return render_to_response("other_userpage.html",
                          {'foruser': foruser, 'branches': branches,
                           'overall': overall, 'entertainment': entertainment,
                           'writing': writing, 'immersiveness': immersiveness,
                           'interest': interest},
                          context_instance=RequestContext(request))
    else:
        return goHome()


def search(request, search_content):
    if not request.user.is_authenticated():
        return goHome()
    branches = Branch.objects.all()
    users = User.objects.all()
    branch_results = []
    user_results = []
    similarity = 70
    Nogo = False
    # Goes through all the branches 30 times, so no branches with less than
    # 70% similarity get in, and steps down the similarty bar each time.
    while similarity <= 100:
        for branch in branches:
            # compares two strings using the fuzzywuzzy git download, and
            # returns a similarity from 0-100
            if fuzz.ratio(str(branch.action),
                    str(search_content)) == similarity:
                branch_results.append(branch)
                branches.exclude(id=branch.id)
                Nogo = True
            if fuzz.partial_ratio(str(branch.action),
              str(search_content)) == similarity and Nogo == False:
                branch_results.append(branch)
                Nogo = False
        similarity += 1
    similarity = 100
    while similarity != 70:
        for user in users:
            if fuzz.ratio(str(user.username),
                    str(search_content)) == similarity:
                user_results.append(user)
            elif fuzz.partial_ratio(str(user.username),
                str(search_content)) == similarity:
                user_results.append(user)
        similarity -= 1
    return render_to_response("search_results.html",
            {'branch_results': branch_results, 'user_results': user_results},
            context_instance=RequestContext(request))


class RichUserCreationForm(UserCreationForm):
    # first_name = forms.CharField(label = "First name")
    # last_name = forms.CharField(label = "Last name")

    def save(self, commit=True):
        user = super(RichUserCreationForm, self).save(commit=False)
        # self.cleaned_data["first_name"]
        first_name = "First"
        # self.cleaned_data["last_name"]
        last_name = "Last"
        user.first_name = first_name
        user.last_name = last_name
        if commit:
            user.save()
            user.has_perm('adventure.add_Branch')
            user.has_perm('adventure.change_Branch')
            user.has_perm('adventure.delete_Branch')
        return user


class TokenRegistrationForm(RichUserCreationForm):
    token = forms.CharField(max_length=20, label="Registration Token")

    def clean_token(self):
        data = self.cleaned_data["token"]
        if data != settings.REGISTRATION_TOKEN:
            raise forms.ValidationError("Incorrect Registration Token!")
        return data


class AccountForm(forms.Form):
    first_name = forms.CharField()
    last_name = forms.CharField()


def edit_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            # form.cleaned_data['first_name']
            request.user.first_name = "First"
            # form.cleaned_data['last_name']
            request.user.last_name = "Last"
            request.user.save()
            return HttpResponseRedirect('/words/')
    else:
        user_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            }
        form = AccountForm(user_data)
    context_dict = {'title': 'Edit Account Settings', 'form': form}
    return render_to_response('account_form.html', context_dict,
         context_instance=RequestContext(request))


def register(request):
    if request.method == 'POST':
        if settings.REGISTRATION_TOKEN:
            form = TokenRegistrationForm(request.POST)
        else:
            form = RichUserCreationForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            return HttpResponseRedirect("/login/")
    else:
        if settings.REGISTRATION_TOKEN:
            form = TokenRegistrationForm()
        else:
            form = RichUserCreationForm()
    return render_to_response("registration/register.html", {'form': form},
            context_instance=RequestContext(request))
