# Top level URL views
from flask import Blueprint, Response, request, redirect, make_response

blueprint = Blueprint('top_views', __name__,
                      template_folder='templates', static_folder='static')
