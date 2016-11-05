import logging
from django.contrib import admin
from django.db import models
from object_permissions import register
from core.models import BlobField
from django.contrib.auth.models import Group, User

__author__ = 'haibin'

logger = logging.getLogger("collie")


class KerberosKeys(models.Model):
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100)
    file = BlobField()

    class Meta:
        db_table = 'kerberos_keys'

admin.site.register(KerberosKeys)


class CollieGroup(Group):
    admins = models.CharField(max_length=1000, default='')
    objects = models.Manager()

    class Meta:
        db_table = 'collie_group'

    def add_admin(self, username):
        admin_list = self.admins.split(",")
        for admin in admin_list:
            if admin == username:
                return True
        admin_list.append(username)
        self.admins = ",".join(admin_list)
        self.save()
        return True

    def has_admin(self, username):
        res = False
        admin_list = self.admins.split(",")
        for admin in admin_list:
            if admin == username:
                res = True
                break
        return res

admin.site.register(CollieGroup)


class GroupRequest(models.Model):
    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)

    class Meta:
        db_table = 'group_request'
        unique_together = (('user', 'group'),)

admin.site.register(GroupRequest)


class Principal(models.Model):
    name = models.CharField(max_length=100, db_index=True, unique=True)
    belong_to = models.SmallIntegerField(max_length=4)
    status = models.SmallIntegerField(max_length=4)

    # get principal list
    @staticmethod
    def get_all_principals():
        return Principal.objects.all()

    @staticmethod
    def get_principal_by_name(name):
        principals = Principal.objects.filter(name=name)
        if len(principals) <= 0:
            return None
        if len(principals) > 1:
            logger.warn('has duplicate name of different principals')
        return principals[0]

    # user apply to principal
    def add_principal(self, user):
        user.set_perms([PRINCIPAL_PERM_USER], self)
        if len(user.get_objects_any_perms(Principal, perms=[PRINCIPAL_PERM_DEFAULT])) <= 0:
            user.set_perms([PRINCIPAL_PERM_DEFAULT], self)
        return True

    # set default principal
    def set_default(self, user):
        principals = user.get_objects_any_perms(Principal, perms=[PRINCIPAL_PERM_DEFAULT])
        for principal in principals:
            user.revoke(PRINCIPAL_PERM_DEFAULT, principal)
        if not user.has_perm(PRINCIPAL_PERM_USER, self):
            logger.info("user %s does not have user perm on principal %s", user, self)
            return False

        user.grant(PRINCIPAL_PERM_DEFAULT, self)

    def __unicode__(self):
        return self.name

    class Meta:
        db_table = 'kerberos_principal'

PRINCIPAL_PERM_DEFAULT = 'default'
PRINCIPAL_PERM_USER = 'user'
register([PRINCIPAL_PERM_DEFAULT, PRINCIPAL_PERM_USER], Principal)
admin.site.register(Principal)


class PrincipalRequest(models.Model):
    user = models.ForeignKey(User)
    principal = models.ForeignKey(Principal)

    @staticmethod
    def apply(user, principal):
        try:
            principal_request = PrincipalRequest(user=user,
                                                 principal=principal)
            principal_request.save()
            return True
        except Exception, ex:
            logger.error("hit exception when apply for principal, %s", ex)
            return False

    @staticmethod
    def cancel(user, principal):
        try:
            requests = PrincipalRequest.objects.filter(user=user, principal=principal)
            for request in requests:
                request.delete()
            return True
        except Exception, ex:
            logger.error("hit exception when cancel principal request, %s", ex)
            return False

    @staticmethod
    def approve(authorizer, applicant, principal):
        try:
            if not authorizer.is_superuser:
                logger.error("authorizer %s is not super user", authorizer)
                return False
            principal.add_principal(applicant)
            return True
        except Exception, ex:
            logger.error("hit exception when approve principal request, %s", ex)
            return False

    def __unicode__(self):
        return "(%s, %s)", self.user, self.principal

    class Meta:
        db_table = 'principal_request'
        unique_together = ('user', 'principal')

admin.site.register(PrincipalRequest)