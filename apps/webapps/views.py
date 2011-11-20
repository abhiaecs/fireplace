from django.shortcuts import get_object_or_404, redirect

import jingo
from mobility.decorators import mobile_template
from tower import ugettext_lazy as _lazy

import amo
from amo.decorators import json_view, login_required, post_required
from amo.helpers import loc
from amo.utils import paginate
from addons.decorators import addon_view
import addons.views
import search.views

from addons.models import Category
from browse.views import category_landing, CategoryLandingFilter
from sharing.views import share as share_redirect
from .models import Webapp

TYPE = amo.ADDON_WEBAPP


def es_app_list(request):
    ctx = search.views.app_search_query(request)
    return jingo.render(request, 'webapps/listing.html', ctx)


# TODO(cvan): Make a mobile apps homepage when we know what we want.
#@mobile_template('webapps/{mobile/}home.html')
def app_home(request):
    if request.MOBILE:
        return redirect('apps.list')

    src = 'cb-btn-home'
    dl_src = 'cb-dl-home'

    base = Webapp.objects.reviewed()
    free = (base.filter(addonpremium__price__price__isnull=True)
            .order_by('-weekly_downloads'))[:18]
    paid = (base.filter(addonpremium__price__price__isnull=False)
            .order_by('-weekly_downloads'))[:18]

    ctx = {
        'section': amo.ADDON_SLUGS[TYPE],
        'addon_type': TYPE,
        'free': free,
        'paid': paid,
        'src': src,
        'dl_src': dl_src,
    }
    return jingo.render(request, 'webapps/home.html', ctx)


class AppCategoryLandingFilter(CategoryLandingFilter):

    opts = (('downloads', _lazy(u'Most Popular')),
            ('rating', _lazy(u'Top Rated')),
            ('created', _lazy(u'Recently Added')),
            ('featured', _lazy(u'Featured')))


class AppFilter(addons.views.BaseFilter):
    opts = (('downloads', _lazy(u'Weekly Downloads')),
            ('free', loc(u'Top Free')),
            ('paid', loc(u'Top Paid')),
            ('rating', _lazy(u'Top Rated')))
    extras = (('created', _lazy(u'Newest')),
              ('name', _lazy(u'Name')),
              ('price', loc(u'Price')),
              ('updated', _lazy(u'Recently Updated')),
              ('hotness', _lazy(u'Up & Coming')))


def app_listing(request):
    qs = Webapp.objects.listed()
    filter = AppFilter(request, qs, 'sort', default='downloads', model=Webapp)
    return filter.qs, filter


@mobile_template('browse/{mobile/}extensions.html')
def app_list(request, category=None, template=None):
    if category is not None:
        q = Category.objects.filter(type=TYPE)
        category = get_object_or_404(q, slug=category)

    sort = request.GET.get('sort')
    if not sort and not request.MOBILE and category and category.count > 4:
        return category_landing(request, category, TYPE,
                                AppCategoryLandingFilter)

    addons, filter = app_listing(request)
    sorting = filter.field
    src = 'cb-btn-%s' % sorting
    dl_src = 'cb-dl-%s' % sorting

    if category:
        addons = addons.filter(categories__id=category.id)

    addons = paginate(request, addons, count=addons.count())
    ctx = {'section': amo.ADDON_SLUGS[TYPE], 'addon_type': TYPE,
           'category': category, 'addons': addons, 'filter': filter,
           'sorting': sorting, 'sort_opts': filter.opts, 'src': src,
           'dl_src': dl_src}
    return jingo.render(request, template, ctx)


def share(request, app_slug):
    webapp = get_object_or_404(Webapp, app_slug=app_slug)
    return share_redirect(request, webapp, webapp.name, webapp.summary)


@json_view
@addon_view
@login_required
@post_required
def record(request, addon):
    if addon.is_webapp():
        installed = addon.get_or_create_install(user=request.amo_user)
        return {'addon': addon.pk,
                'receipt': installed.receipt if installed else ''}
