# from django.contrib.auth.models import User
# from core.models import TreeNode
# from core.models import PermissionConstants

## initialize the data root permissions
#data_root_node = TreeNode.objects.get(id=1)
#admin_user = User.objects.filter(name="admin")
#"""@type admin_user: django.contrib.auth.models.User"""
#admin_user.grant(PermissionConstants.READ, data_root_node)
#admin_user.grant(PermissionConstants.WRITE, data_root_node)
#for admin_group in admin_user.groups.all():
#    admin_group.grant(PermissionConstants.READ, data_root_node)
#    admin_group.grant(PermissionConstants.WRITE, data_root_node)
