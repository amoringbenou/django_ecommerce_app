
# Create your views here.

from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
import json
import datetime
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import *
from .utils import cookieCart, cartData, guestOrder
from .forms import CustomUserCreationForm



def loginUser(request):
    page = 'login'
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        print('Username - ' + username)

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('store')
        else:
            messages.info(request, 'Username or Password is incorrect')
            return redirect('login')
    return render(request, 'store/login_register.html', {'page': page})


def logoutUser(request):
    logout(request)
    return redirect('login')


def registerUser(request):
    page = 'register'
    form = CustomUserCreationForm()
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']
            user = form.save(commit=False)
            user.save()
            Customer.objects.create(
                user=user,
                name=user.username,
                email=user.email
            )
            print(" user saved - -- ")

            if user is not None:
                messages.success(request, "Account was created for " + username)
                return redirect('login')

        else:
            username = request.POST['username']
            email = request.POST['email']
            password1 = request.POST['password1']
            password2 = request.POST['password2']

            try:

                if len(password1) < 8:
                    messages.info(request, "The two passwords must contain at least 8 alphanumerics characters.")
                elif password2 != password1:
                    messages.info(request, "The two passwords fields didn't match .")
                elif User.objects.filter(email=email).exists():
                    messages.info(request, "This email is already used.")
                elif User.objects.filter(username=username).exists():
                    messages.info(request, "This username is already used.")

            except TypeError as error:

                raise ('an error occur when trying to debug ', error)

            return redirect('register')
    else:
        init_values = {'username': request.POST.get('username'), 'email': request.POST.get('email')}
        form = CustomUserCreationForm(initial=init_values)
    context = {'form': form, 'page': page}
    return render(request, 'store/login_register.html', context)


def store(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    products = Product.objects.all()

    ## Pagination

    page = request.GET.get('page', 1)
    paginator = Paginator(products, 9)
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)
        
    context = {'products': products, 'cartItems': cartItems}
    return render(request, 'store/store.html', context)


def product_detail(request, pk):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    product = Product.objects.get(id=pk)
    context = {'product': product, 'cartItems': cartItems}
    return render(request, 'store/product_details.html', context)

@login_required(login_url = 'login')
def cart(request):
    data = cartData(request)
    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request):
    data = cartData(request)

    cartItems = data['cartItems']
    order = data['order']
    items = data['items']

    context = {'items': items, 'order': order, 'cartItems': cartItems}
    return render(request, 'store/checkout.html', context)

@login_required(login_url='login')
def updateItem(request):
    data = json.loads(request.body)
    productId = data['productId']
    action = data['action']
    print('Action:', action)
    print('Product:', productId)

    customer = request.user.customer
    product = Product.objects.get(id=productId)
    order, created = Order.objects.get_or_create(customer=customer, complete=False)

    orderItem, created = OrderItem.objects.get_or_create(order=order, product=product)

    if action == 'add':
        orderItem.quantity += 1
    elif action == 'remove':
        orderItem.quantity -= 1

    orderItem.save()

    if orderItem.quantity <= 0:
        orderItem.delete()

    return JsonResponse('Item was added', safe=False)

@login_required(login_url='login')
def processOrder(request):
    transaction_id = datetime.datetime.now().timestamp()
    data = json.loads(request.body)

    if request.user.is_authenticated:
        customer = request.user.customer
        order, created = Order.objects.get_or_create(customer=customer, complete=False)
    else:
        customer, order = guestOrder(request, data)

    total = float(data['form']['total'])
    order.transaction_id = transaction_id

    if total == order.get_cart_total:
        order.complete = True
    order.save()

    if order.shipping == True:
        ShippingAddress.objects.create(
            customer=customer,
            order=order,
            address=data['shipping']['address'],
            city=data['shipping']['city'],
            state=data['shipping']['state'],
            zipcode=data['shipping']['zipcode'],
        )

    return JsonResponse('Payment submitted..', safe=False)
