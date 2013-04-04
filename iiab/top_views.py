# Top level URL views
from flask import Blueprint, Response, request, redirect, make_response, render_template

from config import config

blueprint = Blueprint('top_views', __name__,
                      template_folder='templates', static_folder='static')


@blueprint.route('/')
def index():
    return render_template("index.html", kiwix_url=config().get('KIWIX', 'url'))
