from django.contrib.auth.models import Group, User
from django.core.exceptions import ObjectDoesNotExist
from core.models import TreeNode, PermissionConstants
import sys

# add admin user to admin group
admin_user_name = "admin"
admin_user = None
try:
    admin_user = User.objects.get(username=admin_user_name)
except ObjectDoesNotExist:
    print admin_user_name + ' does not exist'
    sys.exit(-1)

# create admin group
admin_group = None
try:
    admin_group = Group.objects.get(name='admin')
except ObjectDoesNotExist:
    admin_group = Group(name='admin')
    admin_group.save()

admin_group.user_set.add(admin_user)

# create everyone group
everyone_group = None
try:
    everyone_group = Group.objects.get(name="everyone")
except ObjectDoesNotExist:
    everyone_group = Group(name='everyone')
    everyone_group.save()

everyone_group.user_set.add(admin_user)

# grant permission of data node
root_node = TreeNode.objects.get(id=1)
everyone_group.grant(PermissionConstants.READ, root_node)
everyone_group.grant(PermissionConstants.WRITE, root_node)
admin_user.grant(PermissionConstants.READ, root_node)
admin_user.grant(PermissionConstants.WRITE, root_node)
admin_group.grant(PermissionConstants.READ, root_node)
admin_group.grant(PermissionConstants.WRITE, root_node)

print "\neverything is done successfully\n"