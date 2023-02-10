from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404, HttpRequest, HttpResponseRedirect
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
import datetime

from .models import Book, SearchRecord
from Account.models import PlatformUser

from .RecModel.Recommender import RecSystem


def preprecess_nn(pre=[]):
    """Convert $pre to NN input"""

    res = [0 for i in range(20)]

    # extract category id on the hundredth
    tmp = [0 for i in range(6)]
    for i in range(len(pre)):
        tmp[pre[i] // 100] = tmp[pre[i] // 100] + 1

    # find the 2 favorite categories
    maxid1, maxval = 0, 0
    for i in range(len(tmp)):
        if maxval < tmp[i]:
            maxid1 = i
            maxval = tmp[i]
    res[0] = maxid1
    del tmp[maxid1]
    maxid2, maxval = 0, 0
    for i in range(len(tmp)):
        if maxval < tmp[i]:
            maxid2 = i
            maxval = tmp[i]
    res[10] = maxid2

    tmp1 = 1
    tmp2 = 11
    for i in range(len(pre)):
        if pre[i] // 100 == maxid1:
            if tmp1 < 10:
                res[tmp1] = pre[i] % 100
                tmp1 += 1
        if pre[i] // 100 == maxid2:
            if tmp2 < 20:
                res[tmp2] = pre[i] % 100
                tmp2 += 1

    return res


@login_required(redirect_field_name="login")
def index(request):
    platform_user = PlatformUser.objects.get(uid=request.user)
    rec = RecSystem()
    topk = 1  # How many books to be recommended
    book_list = []

    """ Get user's preference tag_id, store in list $preference """
    preference = []
    preference_query = platform_user.type_preference.filter(platformuser=platform_user)
    for item in preference_query:
        preference.append(item.tag_id)
    print(preference)

    """ NN Recommendation """
    nn_input = preprecess_nn(list(preference))
    """ 
    WARNING: This model may be broken for some reason. It only recommends 
    the first few ones with the smallest id. But it is error-free, so I 
    still make a PR.

    """
    book_list = rec.recommend(nn_input, topk=1, flag=0)

    # TODO: Implement VAE model

    """ Note: $book_list has been filled here. """

    print(book_list)
    return render(request, "Recommendation/index.html", locals())


@login_required(redirect_field_name="login")
def search(request: HttpRequest):
    platform_user = PlatformUser.objects.get(uid=request.user)
    if request.method == "GET" and request.GET:
        book_name = request.GET["name"]
        # TODO: exact fitting now, should be enhanced
        try:
            book_found = Book.objects.get(bookname=book_name)
        except Book.DoesNotExist:
            err_msg = "书目不存在！"
            # TODO: add function: allow user upload books
            return render(request, "Recommendation/search.html", locals())
        record_new = SearchRecord.objects.create(
            searcher=PlatformUser.objects.get(uid=request.user),
            search_tag=book_found.book_tag,
            search_cont=book_name,
            search_time=datetime.datetime.now(),
        )
        err_msg = "搜索成功，以下是该书目详情页面："
    else:
        err_msg = "搜索失败"

    return render(request, "Recommendation/search.html", locals())


@login_required(redirect_field_name="login")
def detailBook(request, book_id):
    platform_user = PlatformUser.objects.get(uid=request.user)
    book = Book.objects.get(id=book_id)
    return render(request, "Recommendation/detailBook.html", locals())


"""
@login_required(redirect_field_name='login')
def detailTopic(request, book_id):
    platform_user = PlatformUser.objects.get(uid=request.user)
    
    return render(request, 'Recommendation/detailTopic.html', locals())
"""
