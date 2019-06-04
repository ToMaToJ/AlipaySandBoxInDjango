import uuid

from django.shortcuts import render, HttpResponse, redirect

from app01 import models, pay


def index(request):
    good_list = models.Goods.objects.all()

    return render(request, "index.html", {"goods_list": good_list})


def buy(request, ids):
    """
    buy, make a payment
    """
    obj = models.Goods.objects.get(id=ids)

    # encrypt the order
    no = str(uuid.uuid4())
    models.Order.objects.create(no=no, goods_id=obj.id)
    alipay = pay.AliPay(
        appid="2016093000629032",
        app_notify_url="http://127.0.0.1:8000/check_order/",
        return_url="http://127.0.0.1:8000/show/",
        app_private_key_path="key/app_private_2048.txt",
        alipay_public_key_path="key/alipay_public_2048.txt",
        debug=True,
    )

    query_params = alipay.direct_pay(
        subject=obj.name,
        out_trade_no=no,
        total_amount=obj.price,
    )
    # 支付宝提供的url网关
    pay_url = "https://openapi.alipaydev.com/gateway.do?{0}".format(query_params)

    return redirect(pay_url)


def check_order(request):
    """
    POST请求，支付宝通知支付信息，我们修改订单状态
    """
    if request.method == 'POST':
        # 全局变量
        alipay = pay.AliPay(
            appid="2016093000629032",  # 注意,改成自己的,在支付宝沙箱环境中
            app_notify_url="http://127.0.0.1:8000/check_order/",  # POST,发送支付状态信息
            return_url="http://127.0.0.1:8000/show/",  # GET,将用户浏览器地址重定向回原网站
            app_private_key_path="key/app_private_2048.txt",
            alipay_public_key_path="key/alipay_public_2048.txt",
            debug=True,  # 默认True测试环境、False正式环境
        )

        from urllib.parse import parse_qs
        body_str = request.body.decode('utf-8')
        post_data = parse_qs(body_str)

        post_dict = {}
        for k, v in post_data.items():
            post_dict[k] = v[0]
        sign = post_dict.pop('sign', None)
        status = alipay.verify(post_dict, sign)
        if status:
            # 支付成功
            out_trade_no = post_dict['out_trade_no']
            models.Order.objects.filter(no=out_trade_no).update(status=2)
            return HttpResponse("支付成功，(ノ｀Д)ノ")
        else:
            return HttpResponse("支付失败，")


def show(request):
    """
    回到我们的页面
    """
    if request.method == "GET":
        alipay = pay.AliPay(
            appid="2016093000629032",  # 注意,改成自己的,在支付宝沙箱环境中
            app_notify_url="http://127.0.0.1:8000/check_order/",  # POST,发送支付状态信息
            return_url="http://127.0.0.1:8000/show/",  # GET,将用户浏览器地址重定向回原网站
            app_private_key_path="key/app_private_2048.txt",
            alipay_public_key_path="key/alipay_public_2048.txt",
            debug=True,  # 默认True测试环境、False正式环境
        )

        params = request.GET.dict()
        print(params)
        sign = params.pop('sign', None)
        status = alipay.verify(params, sign)
        if status:
            return HttpResponse('支付成功')
        else:
            return HttpResponse('失败')
    else:
        return HttpResponse('只支持GET请求')


def order_list(request):
    """
    查看订单状态
    """
    order = models.Order.objects.all()
    return render(request, 'order_list.html', {'orders': order})
