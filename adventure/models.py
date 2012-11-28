from django.db import models
from django.contrib.auth.models import User
from djangoratings.fields import RatingField

class Branch(models.Model):
    action = models.CharField(max_length=30)
    text = models.TextField()
    parent = models.ForeignKey('Branch', blank = True, null=True)
    author = models.ForeignKey(User)
    lastedited = models.DateTimeField(auto_now=True)   
    entertainment = models.DecimalField(max_digits=4, decimal_places=2) #1.00 - 100.00
    writing = models.DecimalField(max_digits=4, decimal_places=2)
    immersiveness = models.DecimalField(max_digits=4, decimal_places=2)
    interest = models.DecimalField(max_digits=4, decimal_places=2)
    voted_ent = models.ManyToManyField(User, related_name='ent_voters', blank=True, null=True)
    voted_wri = models.ManyToManyField(User, related_name='wri_voters', blank=True, null=True)
    voted_imm = models.ManyToManyField(User, related_name='imm_voters', blank=True, null=True)
    voted_int = models.ManyToManyField(User, related_name='int_voters', blank=True, null=True)
    
    def already_voted(self, user, attribute):
        if attribute == "entertainment" or attribute == "ent":
            for branch in user.ent_voters.all():
                if branch == self:
                    return True
        if attribute == "writing" or attribute == "wri":
            for voter in self.voted_wri.all():
                if voter == User:
                    return True
        if attribute == "immersiveness" or attribute == "imm":
            for voter in self.voted_imm.all():
                if voter == User:
                    return True
        if attribute == "interest" or attribute == "int":
            for voter in self.voted_int.all():
                if voter == User:
                    return True
        return False
        
    def kill_branch(self):
        offspring = Branch.objects.all().filter(parent = self.id)
        for branch in offspring:
            branch.kill_branch()
        self.delete()

    def get_overall(self):
        rating = ((self.entertainment + self.writing + self.immersiveness + self.interest)/4)/20
        return rating

    def get_entertainment(self):
        return self.entertainment/20
  
    def get_writing(self):
        return self.writing/20

    def get_immersiveness(self):
        return self.immersiveness/20

    def get_interest(self):
        return self.interest/20

    def __unicode__(self):
        if self.id == 1:
            return str(self.action)+"-"+str(self.id)
        else:
            return str(self.parent.id)+"-"+str(self.action)+"-"+str(self.id)

    class Meta:
        ordering = ['id']

# Create your models here.
