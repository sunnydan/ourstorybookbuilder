from decimal import Decimal
from ourstorybook.adventure.models import Branch
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User


def findBranch(idy, acty):
    branch = None
    if idy == '' or acty == '':
        branch = Branch.objects.all().get(id=1)
    else:
        filtered = Branch.objects.all().filter(parent=idy)
        for branch in filtered:
            if branch.action == str(acty):
                branch = branch
                break
            else:
                branch = None
    return branch


def myBranch(user, branch):
    if branch == None:
        return False
    if user == branch.author:
        return True
    return False


def goHome():
    return HttpResponseRedirect('/')


def getUserRating(user):
    branches = Branch.objects.all().filter(author=user)
    rating = 0
    for branch in branches:
        rating += branch.get_overall()
    if len(branches) != 0:
        rating = rating / len(branches)
    if rating == 0:
        rating = .1
    return rating


def deci(num):
    a = Decimal('%.2f' % num)
    return a
