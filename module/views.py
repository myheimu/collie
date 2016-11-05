# Create your views here.
import base64
import json
import logging
import os
import shutil
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django import forms
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from core.webhdfs import WebHdfs
from module.models import Module, ModuleVersions, UserGit, ModuleHdfsFiles
from git import *
import xml.dom.minidom
from module.resumable_wrapper import ResumableWrapper
from settings import settings
import time

logger = logging.getLogger("collie")
resumable_wrapper = ResumableWrapper()

@login_required()
def index(request):
    user = request.user
    username = user.username

    logger.info("enter module index page, user %s", username)
    modules = Module.objects.filter(status__gte=0).values('name', 'id', 'created_by', 'created_time', 'modify_by',
                                                          'modify_time', 'description', 'wiki_link', 'is_public')
    module_list = []
    for module in modules:
        module_versions = ModuleVersions.objects.filter(module_id=module['id']).values('id', 'module_id', 'refer_count')
        if len(module_versions) <= 0:
            continue

        most_refer_version = module_versions.order_by('-refer_count')[0]
        most_refer_count = most_refer_version['refer_count']
        popularity = min(most_refer_count, 10) * 10

        module_created_by = module['created_by']
        module_is_public = module['is_public']
        module_modify_by = module['modify_by']
        owners = module_modify_by.split(",")

        is_owner = False
        if len(owners) > 0:
            for owner in owners:
                if owner.strip() == username:
                    is_owner = True
                    break

        if module_created_by != username and not module_is_public and not user.is_superuser and not is_owner:
            continue

        module_list.append({
            'name': module['name'],
            'id': module['id'],
            'created_by': module['created_by'],
            'created_time': module['created_time'],
            'popularity': popularity,
            'modify_by': module['modify_by'],
            'modify_time': module['modify_time'],
            'description': module['description'],
            'wiki_link': module['wiki_link'],
        })

    if settings.UPLOAD_MODE != "local_only":
        user_gits = UserGit.objects.filter(username=username).values('git_repository')
        repos = []
        for repo in user_gits:
            repos.append(repo['git_repository'])
    context = {
        'module_list': module_list,
        'upload_mode': settings.UPLOAD_MODE,
        'repositories': repos
    }
    return render_to_response('module/module_index.html', context, context_instance=RequestContext(request))


@login_required()
def manage(request):
    user = request.user
    username = user.username
    module_id = request.GET.get('module_id')
    module = Module.objects.get(id=module_id)
    module_versions = ModuleVersions.objects.all().filter(module_id=module_id, status__gte=0)\
        .values('id', 'comment', 'created_by', 'created_time', 'comment',
                'type', 'file_name', 'options', 'refer_count', 'status')\
        .order_by('-created_time')

    owners = module.modify_by.split(",")
    is_owner = False
    if len(owners) > 0:
        for owner in owners:
            if owner.strip() == username:
                is_owner = True
                break

    module_info = {
        'id': module.id,
        'name': module.name,
        'created_by': module.created_by,
        'created_time': module.created_time,
        'modify_by': module.modify_by,
        'modify_time': module.modify_time,
        'description': module.description,
        'wiki_link': module.wiki_link,
        'is_public': module.is_public,
        'is_owner': (module.created_by == username or is_owner)
    }
    versions_info = []
    for module_version in module_versions:
        refer_count = module_version['refer_count']
        popularity = min(refer_count, 10) * 10
        versions_info.append({
            'id': module_version['id'],
            # 'comment': module_version['comment'],
            'popularity': popularity,
            'created_by': module_version['created_by'],
            'created_time': module_version['created_time']
        })
    if len(module_versions) > 0:
        version_latest = module_versions.order_by('-created_time')[0]
        version_latest_id = version_latest['id']
        version_latest_type = version_latest['type']
    else:
        version_latest_id = -1
        version_latest_type = None

    if settings.UPLOAD_MODE != "local_only":
        user_gits = UserGit.objects.filter(username=username).values('git_repository')
        repos = []
        for repo in user_gits:
            repos.append(repo['git_repository'])
    context = {
        'module': module_info,
        'latest_version_id': version_latest_id,
        'latest_version_type': version_latest_type,
        'version_list': versions_info,
        'upload_mode': settings.UPLOAD_MODE,
        'repositories': repos
    }
    return render_to_response('module/module_manage.html', context, context_instance=RequestContext(request))


@login_required()
@csrf_exempt
def set_public(request):
    username = request.user.username
    module_id = request.POST.get('module_id')
    is_public = request.POST.get('is_public')
    logger.debug("enter set_public, user %s, module id %s, is_public %s", username, module_id, is_public)

    module = Module.objects.get(id=module_id)
    module.is_public = (is_public == 'True')
    # module.modify_by = username
    module.modify_time = timezone.now()
    module.save()

    context = {
        'status': 1,
        'is_public': module.is_public
    }
    logger.debug("exit set_public successfully, res %s", context)
    return HttpResponse(json.dumps(context), mimetype="application/json")


class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=1024)
    file = forms.FileField()


@login_required()
@csrf_exempt
def upload(request):
    username = request.user.username

    if settings.UPLOAD_MODE == "git_only":
        context = {
            "status": -1,
            "error": "only allow to upload from git"
        }
        return HttpResponse(json.dumps(context), content_type='application/json')

    resumable_identifier = request.REQUEST.get("resumableIdentifier")
    resumable_chunk_number = int(request.REQUEST.get("resumableChunkNumber"))
    resumable_chunk_size = int(request.REQUEST.get("resumableChunkSize"))
    resumable_total_size = long(request.REQUEST.get("resumableTotalSize"))
    resumable_file_name = request.REQUEST.get("resumableFilename")
    logger.info("get info when upload by user %s, chunk number %d, method %s", username,
                resumable_chunk_number, request.method)

    if request.method == 'POST':
        file_content = request.body
        logger.info("start to write chunk number %s", resumable_chunk_number)
        resumable_wrapper.write(resumable_identifier, resumable_chunk_number, resumable_chunk_size,
                                resumable_total_size, resumable_file_name, file_content)
        logger.info("end of write chunk number %s", resumable_chunk_number)
        if resumable_wrapper.is_finished(resumable_identifier):
            logger.info("start to remove coz finished")
            resumable_wrapper.remove(resumable_identifier)
            return HttpResponse("All finished.")
        else:
            logger.info("finish of upload chunk number %d", resumable_chunk_number)
            return HttpResponse("Upload")
    elif request.method == 'GET':
        logger.info("start to check uploaded of chunk number %d", resumable_chunk_number)
        if resumable_wrapper.is_uploaded(resumable_identifier, resumable_chunk_number):
            logger.info("file uploaded of chunk number %d", resumable_chunk_number)
            return HttpResponse("Uploaded.")
        else:
            logger.info("file not uploaded of chunk number %d", resumable_chunk_number)
            return HttpResponse(status=404)


@login_required()
@csrf_exempt
def git_history(request):
    username = request.user.username
    logger.info("user %s query git versions", username)

    repository = request.GET.get("repository")
    branch = "master"
    repoFolder = repository.split("/")[-1]
    repoTmpDir = settings.GIT_REPOSITORY_PATH + username + "/" + repoFolder
    try:
        repo = Repo.clone_from(repository, repoTmpDir)
        logger.info("clone from %s successfully", repository)
    except GitCommandError as e1:
        #can't clone repository or repository already exists
        try:
            repo = Repo(repoTmpDir)
            logger.info("find repository from local dir: %s", repoTmpDir)
        except NoSuchPathError as e2:
            context = {
                "status": -1,
                "error": "can't clone from [" + repository + "]"
            }
            return HttpResponse(json.dumps(context), content_type='application/json')

    repo.git.checkout(branch)
    repo.git.pull()
    repo.git.checkout("HEAD")

    logger.info("checkout repository: %s branch: %s version: HEAD", repository, branch)

    commits = repo.iter_commits(max_count=10)
    history = []
    for commit in commits:
        history.append(commit.hexsha[0:9])
    context = {
        "status": 1,
        "history": history
    }
    return HttpResponse(json.dumps(context), content_type='application/json')

@login_required()
@csrf_exempt
def git_build(request):
    username = request.user.username
    logger.info("user %s query git build type", username)

    repository = request.GET.get("repository")
    #branch = request.GET.get("branch")
    branch = "master"
    version = request.GET.get("version")

    repoFolder = repository.split("/")[-1]
    repoTmpDir = settings.GIT_REPOSITORY_PATH + username + "/" + repoFolder
    try:
        repo = Repo.clone_from(repository, repoTmpDir)
        logger.info("clone from %s successfully", repository)
    except GitCommandError:
        #can't clone repository or repository already exists
        try:
            repo = Repo(repoTmpDir)
            logger.info("find repository from local dir: %s", repoTmpDir)
        except NoSuchPathError:
            context = {
                "status": -1,
                "error": "can't clone from [" + repository + "]"
            }
            return HttpResponse(json.dumps(context), content_type='application/json')

    repo.git.checkout(branch)
    repo.git.pull()
    repo.git.checkout(version)

    logger.info("checkout repository: %s branch: %s version: %s", repository, branch, version)

    confFile = repoTmpDir + "/collie_build.xml"
    try:
        builds = confParser(confFile)
        buildNameList = []
        for build in builds:
            buildNameList.append(build['name'])
    except NoSuchPathError as e:
        logger.info(e)
        context = {
            "status": -1,
            "error": "can't find file: collie_build.xml"
        }
        return HttpResponse(json.dumps(context), content_type='application/json')

    context = {
        "status": 1,
        "buildList": buildNameList
    }
    return HttpResponse(json.dumps(context), content_type='application/json')

@login_required()
@csrf_exempt
def git_upload(request):
    username = request.user.username
    logger.info("user %s upload file from git", username)

    if settings.UPLOAD_MODE == "local_only":
        context = {
            "status": -1,
            "error": "only allow to upload from local file"
        }
        return HttpResponse(json.dumps(context), content_type='application/json')
    repository = request.POST.get("repository")
    branch = request.POST.get("branch")
    version = request.POST.get("version")
    buildName = request.POST.get("build")
    if UserGit.objects.filter(username=username, git_repository=repository).count() == 0:
        context = {
            "status": -1,
            "error": "you doesn't have permission to access [" + repository + "]"
        }
        return HttpResponse(json.dumps(context), content_type='application/json')
    repoFolder = repository.split("/")[-1]
    repoTmpDir = settings.GIT_REPOSITORY_PATH + username + "/" + repoFolder
    try:
        repo = Repo.clone_from(repository, repoTmpDir)
        logger.info("clone from %s successfully", repository)
    except GitCommandError:
        #can't clone repository or repository already exists
        try:
            repo = Repo(repoTmpDir)
            logger.info("find repository from local dir: %s", repoTmpDir)
        except NoSuchPathError:
            context = {
                "status": -1,
                "error": "can't clone from [" + repository + "]"
            }
            return HttpResponse(json.dumps(context), content_type='application/json')

    repo.git.checkout(branch)
    repo.git.pull()
    repo.git.checkout(version)

    confFile = repoTmpDir + "/collie_build.xml"
    try:
        builds = confParser(confFile)
        for build in builds:
            if buildName == build['name']:
                cmd = "cd " + repoTmpDir + ";" + build['cmd']
                logger.info("build cmd: %s", cmd)
                if os.system(cmd) !=0 :
                    context = {
                        "status": -1,
                        "error": "build cmd error"
                    }
                    return HttpResponse(json.dumps(context), content_type='application/json')
                targetFile = repoTmpDir + "/" + build['target']
                if not os.path.exists(targetFile):
                    raise NoSuchPathError("can't find target file")
                targetFileName = os.path.basename(targetFile)
                if default_storage.exists(targetFileName):
                    default_storage.delete(targetFileName)
                path = default_storage.save(targetFileName, ContentFile(open(targetFile).read()))
                logger.info(path)
                break

    except (NoSuchPathError, KeyError) as e:
        logger.info(e)
        context = {
            "status": -1,
            "error": "can't parse collie_build.xml"
        }
        return HttpResponse(json.dumps(context), content_type='application/json')

    context = {
        "status": 1,
        "file_name": targetFileName
    }
    return HttpResponse(json.dumps(context), content_type='application/json')


def handle_uploaded_file(file_name, f, blob_index, is_last):
    with open(settings.MEDIA_PATH + file_name + "." + str(blob_index), 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    blob_size = 0
    is_succeed = False
    if is_last:
        for i in range(0, 3):
            try:
                blob_size = blob_index
                assemble_uploaded_file(file_name, blob_index)
                is_succeed = True
                return
            except IOError as e:
                logger.error(e)
                if i < 2:
                    time.sleep(5)
                else:
                    raise e
            finally:
                if i >= 2 or is_succeed:
                    for j in range(0, blob_size):
                        blob_file_path = settings.MEDIA_PATH + file_name + "." + str(j)
                        if os.path.exists(blob_file_path):
                            logger.info("delete blob %s", file_name + "." + str(j))
                            os.remove(settings.MEDIA_PATH + file_name + "." + str(j))


def assemble_uploaded_file(file_name, blob_size):
    with open(settings.MEDIA_PATH + file_name, 'wb+') as final_destination:
        for i in range(0, blob_size + 1):
            shutil.copyfileobj(open(settings.MEDIA_PATH + file_name + "." + str(i), 'rb+'), final_destination)
            # os.remove(settings.MEDIA_PATH + file_name + "." + str(i))


@login_required()
@csrf_exempt
def save(request):
    username = request.user.username

    # create module
    module_name = request.POST.get("name")
    module_description = request.POST.get('description')
    module_wiki_link = request.POST.get('wiki_link')
    module = Module.create(module_name, module_description, module_wiki_link, username)

    # create module
    # version_comment = request.POST.get('comment')
    version_type = request.POST.get("type")
    version_file = request.POST.get("file")
    version_file_identifier = request.POST.get("file_identifier")
    version_options = request.POST.get("options")
    version_git_options = request.POST.get("git_options")

    try:
        logger.info("save new module, file %s, identifier %s", version_file, version_file_identifier)
        module_version = ModuleVersions.create(module.id, '',
                                               version_type, version_file, version_git_options,
                                               False, version_options, username)
        if not version_file_identifier:
            resumable_wrapper.remove(version_file_identifier)
        logger.debug("module saved")
    except ObjectDoesNotExist as e:
        context = {
            'status': -1,
            'error': 'please upload file first'
        }
        return HttpResponse(json.dumps(context), mimetype="application/json")

    context = {
        'status': 1,
        'module_id': module.id,
        'version_id': module_version.id
    }
    return HttpResponse(json.dumps(context), mimetype="application/json")


@login_required()
@csrf_exempt
def delete(request):
    module_id = request.POST.get('module_id')
    module = Module.objects.get(id=module_id)
    module.status = -1
    module.save()

    context = {"status": 1}
    return HttpResponse(json.dumps(context), mimetype="application/json")


@login_required()
@csrf_exempt
def new_version(request):
    username = request.user.username
    module_id = request.POST.get('module_id')

    # create module version
    # version_comment = request.POST.get('comment')
    version_type = request.POST.get("type")
    version_file = request.POST.get("file")
    version_file_identifier = request.POST.get("file_identifier")
    version_keep_old_file = request.POST.get("keep_old_file") == 'true'
    version_options = request.POST.get("options")
    version_git_options = request.POST.get("git_options")
    try:
        logger.info("new module version, file %s, identifier %s", version_file, version_file_identifier)
        ModuleVersions.create(module_id, "", version_type, version_file, version_git_options,
                              version_keep_old_file, version_options, username)
        if not version_file_identifier:
            resumable_wrapper.remove(version_file_identifier)
    except ObjectDoesNotExist:
        context = {
            'status': -1,
            'error': 'please upload file first'
        }
        return HttpResponse(json.dumps(context), mimetype='application/json')

    context = {
        'status': 1,
        'module_id': module_id
    }
    return HttpResponse(json.dumps(context), mimetype='application/json')


@login_required()
@csrf_exempt
def delete_version(request):
    username = request.user.username
    version_id = request.POST.get('version_id')

    try:
        module_version = ModuleVersions.objects.get(id=version_id)
        module_version.status = -1
        module_version.save()
        context = {
            'status': 1
        }
        logger.info("module version %s deleted by %s", version_id, username)
        return HttpResponse(json.dumps(context), mimetype='application/json')
    except ObjectDoesNotExist:
        context = {
            'status': 1
        }
        return HttpResponse(json.dumps(context), mimetype='application/json')


@login_required()
def version_detail(request):
    version_id = request.GET.get('version_id')
    version = ModuleVersions.objects.get(id=version_id)

    context = {'status': 1,
               'type': version.type,
               'options': json.loads(version.options)}
    return HttpResponse(json.dumps(context), mimetype='application/json')


@login_required()
def download(request):
    version_id = request.GET.get('version_id')
    version = ModuleVersions.objects.get(id=version_id)
    file_name = version.file_name

    if settings.REPOSITORY_SAVE_MODE == settings.REPOSITORY_SAVE_MODE_HDFS and version.hdfs_file_id > 0:
        hdfs_file = ModuleHdfsFiles.objects.get(id=version.hdfs_file_id)
        file_name = hdfs_file.name.strip()
        checksum = hdfs_file.checksum.strip()
        hdfs_path = hdfs_file.path.strip()
        module_version_folder = settings.MEDIA_PATH + "/modules/" + checksum + "/"
        if not os.path.exists(module_version_folder):
            os.makedirs(module_version_folder)

        logger.info("starting to copy remote to local, %s -> %s", hdfs_path, module_version_folder)
        webhdfs = WebHdfs()
        webhdfs.copyToLocal(hdfs_path, module_version_folder)
        local_file_path = module_version_folder + file_name + "_" + checksum
        file_content = open(local_file_path, 'rb').read()
    else:
        version_file = version.file
        file_content = base64.b64decode(version_file)

    # generate the file
    response = HttpResponse(file_content)
    response['Content-Disposition'] = 'attachment; filename=' + file_name
    return response


@login_required()
def latest(request):
    module_id = request.GET.get('module_id')
    module = Module.objects.get(id=module_id)
    module_latest_version = ModuleVersions.objects.filter(status=0).order_by('created_time')[0]

    context = {
        'status': 1,
        'module': {
            'id': module.id,
            'name': module.name,
            'description': module.description
        },
        'version': {
            'id': module_latest_version.id,
            'type': module_latest_version.type,
            'comment': module_latest_version.comment,
            'file_name': module_latest_version.file_name,
            'parameters': json.loads(module_latest_version.parameters)
        }
    }
    return HttpResponse(json.dumps(context), mimetype='application/json')


@login_required()
def detail(request):
    module_id = request.GET.get("module_id")
    version_id = request.GET.get('version_id')
    module = Module.objects.get(id=module_id)

    res_json = dict()
    res_json['status'] = 1
    res_json['name'] = module.name
    res_json['description'] = module.description

    # module versions
    module_versions = ModuleVersions.objects.filter(module_id=module_id, status__gte=0).order_by('-created_time')\
        .values('id', 'type', "git_options", 'options', 'file_name')
    versions = []
    for module_version in module_versions:
        versions.append({
            'id': module_version['id']
        })
    res_json['versions'] = versions

    # latest version parameters
    if len(module_versions) > 0:
        selected_version = module_versions[0] if version_id <= 0 else ModuleVersions.objects\
            .values('type', 'options', 'git_options', 'file_name').get(id=version_id)
        options = json.loads(selected_version['options'])
        git_options_str = selected_version['git_options']
        if git_options_str:
            res_json['git_options'] = json.loads(git_options_str)
        res_json['latest_type'] = selected_version['type']
        res_json['latest_options'] = options
        res_json['latest_file_name'] = selected_version['file_name']
    return HttpResponse(json.dumps(res_json), mimetype="application/json")


@csrf_exempt
@login_required()
def update_owner(request):
    username = request.user.username
    module_id = request.POST.get('module_id')
    owner = request.POST.get('owner')

    try:
        module = Module.objects.get(id=module_id)
        module.modify_by = owner
        module.modify_time = timezone.now()
        module.save()
        context = {
            'status': 1
        }
    except ObjectDoesNotExist as e:
        context = {
            'status': -1,
            'error': 'module not exist'
        }
    return HttpResponse(json.dumps(context), mimetype='application/json')


@csrf_exempt
@login_required()
def update_description(request):
    username = request.user.username
    module_id = request.POST.get('module_id')
    description = request.POST.get('description')

    try:
        module = Module.objects.get(id=module_id)
        module.description = description
        # module.modify_by = username  // we hack modify_by as owners
        module.modify_time = timezone.now()
        module.save()
        context = {
            'status': 1
        }
    except ObjectDoesNotExist as e:
        context = {
            'status': -1,
            'error': 'module not exist'
        }
    return HttpResponse(json.dumps(context), mimetype='application/json')


@csrf_exempt
@login_required()
def update_wiki_link(request):
    username = request.user.username
    module_id = request.POST.get('module_id')
    wiki_link = request.POST.get('wiki_link')

    try:
        module = Module.objects.get(id=module_id)
        module.wiki_link = wiki_link
        # module.modify_by = username // we hack modify_by as owners
        module.modify_time = timezone.now()
        module.save()
        context = {
            'status': 1
        }
    except ObjectDoesNotExist as e:
        context = {
            'status': -1,
            'error': 'module not exist'
        }
    return HttpResponse(json.dumps(context), mimetype='application/json')


def confParser(confFile):
    result = []
    if os.path.exists(confFile):
        dom = xml.dom.minidom.parse(confFile)
        for item in dom.documentElement.getElementsByTagName("module"):
            build = {}
            build["name"] = item.getElementsByTagName("name")[0].childNodes[0].nodeValue
            build["cmd"] = item.getElementsByTagName("cmd")[0].childNodes[0].nodeValue
            build["target"] = item.getElementsByTagName("target")[0].childNodes[0].nodeValue
            result.append(build)
    else:
        raise NoSuchPathError("No such file: " + confFile)

    return result
