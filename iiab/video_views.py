# Video URL views
from flask import (Blueprint, Response, render_template,
                   send_file, make_response)
import json
import os
import string

from config import config
import khan

blueprint = Blueprint('video_views', __name__,
                      template_folder='templates', static_folder='khanvideo')


tree_cache = None


def get_tree():
    global tree_cache
    #khan_webm_dir = config().get_path('VIDEO', 'khan_webm_dir')
    #khan_cache_file = config().get_path('VIDEO', 'khan_cache_file')
    if tree_cache is None:
        tree_cache = get_tree_from_filesystem()
    return tree_cache


def get_tree_from_filesystem():
    khan_webm_dir = config().get_path('VIDEO', 'khan_webm_dir')
    return khan.find_khan(khan_webm_dir)


def split_khanpath(khanpath):
    return [int(x) for x in khanpath.split('/') if x != '']


def join_khanpath(khanpath):
    return string.join([str(x) for x in khanpath], '/')


@blueprint.route('/khanjson/')
@blueprint.route('/khanjson/<path:khanpath>/')
def khan_json_view(khanpath=''):
    path = split_khanpath(khanpath)
    tree = get_tree()
    name, subtree = khan.get(tree, path)
    r = khan.getchildren(tree, path)
    return Response(json.dumps(r, indent=4), mimetype="application/json")


@blueprint.route('/')
@blueprint.route('/khan/')
@blueprint.route('/khan/<path:khanpath>/')
def khan_view(khanpath=''):
    path = split_khanpath(khanpath)
    tree = get_tree()
    name, subtree = khan.get(tree, path)
    r = khan.getchildren(tree, path)
    if 'children' in r:
        def childmap(child):
            return {
                'index': child[0],
                'name': child[1],
                'url': "/iiab/video/khan/" + join_khanpath(path + [child[0]])
            }
        children = map(childmap, r['children'])
        return render_template('khan_index.html', breadcrumbs=r['breadcrumbs'], children=children)
    elif 'file' in r:
        base_url = config().get('VIDEO', 'video_url')
        webm = base_url + '/' + khanpath + ".webm"
        h264 = base_url + '/' + khanpath + ".m4v"
        title = r['breadcrumbs'][-1][1]
        return render_template('khan_video.html', breadcrumbs=r['breadcrumbs'],
                               webm=webm, h264=h264, title=title)
    else:
        raise Exception("Unknown return type in Khan Academy tree")


@blueprint.route('/khanvideo/<path:khanpath>.webm')
def khan_webm_view(khanpath=''):
    print "webm_view", khanpath
    path = split_khanpath(khanpath)
    tree = get_tree()
    filename = khan.getfile(tree, path)
    khan_webm_dir = config().get_path('VIDEO', 'khan_webm_dir')
    r = send_file(os.path.abspath(os.path.join(khan_webm_dir, filename)))
    return make_response(r, 200, {'Accept-Ranges': 'bytes'})


@blueprint.route('/khanvideo/<path:khanpath>.m4v')
def khan_h264_view(khanpath=''):
    path = split_khanpath(khanpath)
    tree = get_tree()
    filename = khan.getfile(tree, path)
    filename = os.path.splitext(filename)[0] + '.m4v'
    khan_webm_dir = config().get_path('VIDEO', 'khan_h264_dir')
    r = send_file(os.path.abspath(os.path.join(khan_webm_dir, filename)), mimetype='video/mp4')
    return make_response(r, 200, {'Accept-Ranges': 'bytes'})
