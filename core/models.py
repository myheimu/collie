from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils import timezone
from object_permissions import register
from django.contrib.auth.models import Group
import logging
import re
from core import tree

logger = logging.getLogger("collie")

DATABASE_ENGINE = 'django.db.backends.mysql'


# refer to http://softwaremaniacs.org/forum/django/33207/
class BlobField(models.Field):
    description = "LongBlob data type in mysql"

    def db_type(self, connection):
        if DATABASE_ENGINE == 'django.db.backends.mysql':
            return 'LONGBLOB'
        else:
            raise NotImplementedError

    def to_python(self, value):
        return value

    def get_db_prep_save(self, value, connection):
        db_value = str(bytearray(value))
        return db_value

from south.modelsinspector import add_introspection_rules
add_introspection_rules([], ["^core\.models\.BlobField"])


class NodePermission(object):
    owner_read = False
    owner_write = False
    group_read = False
    group_write = False
    all_read = False
    all_write = False

    def __init__(self, permission_str):
        """
        @type permission_str: str
        """
        # valid format of permission_str like: rwr-r-
        permission_str_pattern = re.compile(r'[rw\-]{6}')
        match = permission_str_pattern.match(permission_str)
        if not match:
            raise Exception("input %s is not valid" % permission_str)
        self.owner_read = NodePermission.has_perm(0, permission_str[0])
        self.owner_write = NodePermission.has_perm(1, permission_str[1])
        self.group_read = NodePermission.has_perm(2, permission_str[2])
        self.group_write = NodePermission.has_perm(3, permission_str[3])
        self.all_read = NodePermission.has_perm(4, permission_str[4])
        self.all_write = NodePermission.has_perm(5, permission_str[5])

    @staticmethod
    def has_perm(permission_index, permission_char):
        if permission_index % 2 == 0:
            if permission_char == 'r':
                return True
            elif permission_char == '-':
                return False
            else:
                raise Exception("permission format is invalid")
        else:
            if permission_char == 'w':
                return True
            elif permission_char == '-':
                return False
            else:
                raise Exception("permission format is invalid")


class PermissionConstants(object):
    READ = "read"
    WRITE = "write"


# encoding: UTF-8
class TreeNode(models.Model):
    name = models.CharField(max_length=200)
    creator_name = models.CharField(max_length=200)
    parent_id = models.IntegerField(max_length=11)
    children_ids = models.CharField(max_length=600)
    permission_code = models.CharField(max_length=200)
    permission_group = models.CharField(max_length=200)
    type = models.SmallIntegerField(choices=((1, u'folder'), (2, u'data_leaf'), (3, u'model_leaf')))
    leaf_id = models.IntegerField(max_length=11, default=-1)
    description = models.CharField(max_length=2000)
    status = models.SmallIntegerField(choices=((0, u'deleted'), (1, u'alive')))
    create_time = models.DateTimeField("data node create time")
    modify_time = models.DateTimeField("data node modify time")
    delete_time = models.DateTimeField("data node delete time", default="2010-01-01T17:41:28+00:00")

    def new_node(self, creator_user, name, node_type, description, permission_code, perm_group, leaf_id):
        """
        @type creator_user: django.contrib.auth.models.User
        @type permission_code: str
        @type perm_group: django.contrib.auth.models.Group
        """
        # self node type MUST be folder
        if self.type != 1:
            raise Exception("current node type is not folder")

        if self.status != 1:
            raise Exception("current node does not exist")

        permissions = creator_user.get_all_permissions(self)
        if PermissionConstants.WRITE not in permissions:
            raise Exception("no permission to create sub-item")

        creator_name = creator_user.get_username()
        sub_node = TreeNode(name=name,
                            creator_name=creator_name,
                            parent_id=self.id,
                            children_ids="",
                            permission_code=permission_code,
                            permission_group=perm_group.name,
                            type=node_type,
                            leaf_id=leaf_id,
                            description=description,
                            status=1,
                            create_time=timezone.now(),
                            modify_time=timezone.now())
        sub_node.save()

        children_ids = self.children_ids
        children_id_set = children_ids.split(" ")
        children_id_set.append(str(sub_node.id))
        self.children_ids = " ".join(children_id_set)
        self.save()

        node_permission = NodePermission(permission_code)
        if node_permission.owner_read:
            creator_user.grant(PermissionConstants.READ, sub_node)
        if node_permission.owner_write:
            creator_user.grant(PermissionConstants.WRITE, sub_node)
        if node_permission.group_read:
            perm_group.grant(PermissionConstants.READ, sub_node)
        if node_permission.group_write:
            perm_group.grant(PermissionConstants.WRITE, sub_node)
        if node_permission.all_read:
            everyone_group = Group.objects.filter(name="everyone")
            everyone_group.grant(PermissionConstants.READ, sub_node)
        if node_permission.all_write:
            everyone_group = Group.objects.filter(name="everyone")
            everyone_group.grant(PermissionConstants.WRITE, sub_node)

        logger.info("new node %s created under %s by %s", name, self.name, creator_name)
        return sub_node

    def delete(self, operator_user):
        """
        @type operator_user: django.contrib.auth.models.User
        """
        parent_id = self.parent_id
        parent_node = TreeNode.objects.get(id=parent_id)
        write_perm = operator_user.has_perm(PermissionConstants.WRITE, parent_node)
        if not write_perm:
            raise Exception("has no permission to delete under folder %s" % parent_node.name)

        self.status = 0
        self.save()
        children_ids = parent_node.children_ids
        children_id_list = children_ids.split(" ")
        children_id_list.remove(str(self.id))
        parent_node.children_ids = " ".join(children_id_list)
        parent_node.save()

        logger.info("delete %s under %s by %s", self.name, parent_node.name, operator_user.get_username())
        return True

    def update_fields(self, operator_user, name, description):
        """
        @type operator_user: django.contrib.auth.models.User
        """
        if not operator_user.has_perm(PermissionConstants.WRITE, self):
            raise Exception("%s has no permission to update %s", operator_user.get_username(), self.name)

        has_change = False
        if self.name != name:
            self.name = name
            has_change = True
        if self.description != description:
            self.description = description
            has_change = True

        if has_change:
            self.save()

        logger.info("%s has updated node, name %s, desc %s", operator_user.get_username(), name, description)
        return True

    def delete(self, operator_user):
        """
        @type operator_user: django.contrib.auth.models.User
        """
        parent_id = self.parent_id
        try:
            parent_node = TreeNode.objects.get(id=parent_id)
        except ObjectDoesNotExist:
            raise Exception("parent node is not exist for node %s" % self.name)

        if not operator_user.has_perm(PermissionConstants.WRITE, parent_node):
            raise Exception("no permission to delete this node")

        children_ids_str = parent_node.children_ids
        children_ids_list = children_ids_str.split(" ")
        try:
            children_ids_list.remove(str(self.id))
        except ValueError:
            pass
        parent_node.children_ids = " ".join(children_ids_list)
        parent_node.save()

        self.status = 0
        self.save()

        logger.info("delete node %s by user %s", self.name, operator_user.get_username())
        return True

    def get_children_tree(self, operator_user):
        """
        @type operator_user: django.contrib.auth.models.User
        """
        children_ids_str = self.children_ids
        children_ids_list = children_ids_str.split(" ")

        if not operator_user.has_perm(PermissionConstants.READ, self):
            raise Exception("no permission to get children of %s by %s" %
                            (self.name, operator_user.get_username()))

        children_tree = tree.tree()
        index = 0
        for child in children_ids_list:
            if child.strip() == "":
                continue

            try:
                child_node = TreeNode.objects.get(id=int(child.strip()))
            except ObjectDoesNotExist:
                continue

            if child_node.status != 1:
                continue

            children_tree[index]["id"] = child_node.id
            children_tree[index]["name"] = child_node.name
            children_tree[index]["type"] = child_node.type
            if child_node.children_ids != "":
                children_tree[index]["has_children"] = True

            index += 1

        return children_tree

    def update_permission(self, operator_user, permission, perm_group):
        """
        @type operator_user: django.contrib.auth.models.User
        """
        if self.creator_name != operator_user.get_username():
            raise Exception("no permission to change permission of %s by %s" %
                            (self.name, operator_user.get_username()))

        future_permission = NodePermission(permission)
        if self.permission_group != "":
            current_permission_group_name = self.permission_group
            current_permission_group = Group.objects.filter(name=current_permission_group_name)
            current_permission_group.revoke_all(self)
        everyone_group = Group.objects.filter(name="everyone")
        everyone_group.revoke_all(self)
        operator_user.revoke(self)

        if future_permission.owner_read:
            operator_user.grant(PermissionConstants.READ, self)
        if future_permission.owner_write:
            operator_user.grant(PermissionConstants.WRITE, self)
        if future_permission.group_read:
            perm_group.grant(PermissionConstants.READ, self)
        if future_permission.group_write:
            perm_group.grant(PermissionConstants.WRITE, self)
        if future_permission.all_read:
            everyone_group.grant(PermissionConstants.READ, self)
        if future_permission.all_write:
            everyone_group.grant(PermissionConstants.WRITE, self)

        return True


register([PermissionConstants.READ, PermissionConstants.WRITE], TreeNode)
