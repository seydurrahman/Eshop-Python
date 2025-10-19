from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .forms import RegistrationForm, RatingForm, CheckoutForm
from .models import Product, Category, Cart, Rating, Order
from . import models
from django.db.models import Min, Max, Q, Avg
from . import forms
from . import sslcommerz


# Create your views here.
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful.")
            # Redirect to a success page.
            return redirect("")
        else:
            # Return an 'invalid login' error message.
            messages.error(request, "Invalid username or password")
        # Handle login logic here
    return render(request, "")


def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form = form.save()
            login(request, form)
            messages.success(request, "Registration successful.")
            return redirect("")  # Redirect to a success page.
        else:
            form = RegistrationForm()
    return render(request, "", {"form": form})


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("")


def home(request):
    featured_products = models.Product.objects.filter(available=True).order_by("-created_at")[:8]
    categories = models.Category.objects.all()
    return render(request, "", {"featured_products": featured_products, "categories": categories})

def product_list(request, category_slug=None):
    category = None
    categories = models.Category.objects.all()
    products = models.Product.objects.all()
    if category_slug:
        category = get_object_or_404(models.Category, category_slug)
        products = products.filter(category=category)

        min_price = products.aggregate(Min('price'))['min__price']
        max_price = products.aggregate(Max('price'))['max__price']

        if request.GET.get('min_price'):
            products = products.filter(price__gte=request.GET.get('min_price'))
        if request.GET.get('max_price'):
            products = products.filter(price__lte=request.GET.get('max_price'))
        if request.GET.get('rating'):
            products = products.annotate(avg_rating=Avg('ratings__rating')).filter(avg_rating__gte=request.GET.get('rating'))
        if request.GET.get('search'):
            query = request.GET.get('search')
            products = products.filter(
                Q(name__icontains=query) | 
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            ).distinct()

    return render(request, "", {"category": category, "categories": categories, "products": products, "min_price": min_price, "max_price": max_price})

def product_detail(request,slug):
    product = get_object_or_404(models.Product, slug=slug)
    related_products = models.Product.objects.filter(category=product.category).exclude(id=product.id)
    user_rating = None
    if request.user.is_authenticated:
        try:
            user_rating = models.Rating.objects.get(product=product, user=request.user)
        except models.Rating.DoesNotExist:
            pass

    rating_form = RatingForm(instance=user_rating)
    return render(request, "", {"product": product, "related_products": related_products, "rating_form": rating_form, "user_rating": user_rating})

def rate_product(request, product_id):
    product = get_object_or_404(models.Product, id=product_id)
    
    ordered_items = models.OrderItem.objects.filter(order__user=request.user, product=product, order__paid=True)

    if not ordered_items.exists():
        messages.error(request, "You can only rate products you have purchased.")
        return redirect("",)
    try:
        rating = models.Rating.objects.get(product=product, user=request.user)
    except models.Rating.DoesNotExist:   
        rating = None
    
    if request.method == "POST":
        form = RatingForm(request.POST, instance=rating)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.product = product
            rating.user = request.user
            rating.save()
            messages.success(request, "Your rating has been submitted.")
            return redirect("",)
    else:
        form = RatingForm(instance=rating)
    return render(request, "", {"form": form, "product": product})

def cart_add(request, product_id):
    product = get_object_or_404(models.Product, id=product_id)
    
    try:
        cart = models.Cart.objects.get(user=request.user)
    except models.Cart.DoesNotExist:
        cart = models.Cart.objects.create(user=request.user)
    try:
        cart_item = models.CartItem.objects.get(cart=cart, product=product)
        cart_item.quantity += 1
        cart_item.save()
    except models.CartItem.DoesNotExist:
        cart_item = models.CartItem.objects.create(cart=cart, product=product, quantity=1)
    messages.success(request, f"Added {product.name} to your cart.")
    return redirect(request,"")

def cart_update(request, product_id):
    cart = get_object_or_404(models.Cart, user=request.user)
    product = get_object_or_404(models.Product, id=product_id)
    cart_item = get_object_or_404(models.CartItem, cart=cart, product=product)
    
    quantity = int(request.POST.get("quantity", 1))

    if quantity <= 0:
        cart_item.delete()
        messages.success(request, f"Removed {product.name} from your cart.")
    else:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, f"Updated {product.name} quantity to {quantity}.")
    return redirect(request,"")

def cart_remove(request, product_id):
    cart = get_object_or_404(models.Cart, user=request.user)
    product = get_object_or_404(models.Product, id=product_id)
    cart_item = get_object_or_404(models.CartItem, cart=cart, product=product)
    cart_item.delete()
    messages.success(request, f"Removed {product.name} from your cart.")
    return redirect(request,"")

def cart_detail(request):
    try:
        cart = models.Cart.objects.get(user=request.user)
    except models.Cart.DoesNotExist:
        cart = models.Cart.objects.create(user=request.user)
    return render(request, "", {"cart": cart})

def checkout(request):
    try:
        cart = models.Cart.objects.get(user=request.user)
    except models.Cart.DoesNotExist:
        messages.error(request, "Your cart is empty.")
        return redirect("")

    if request.method == "POST":
        try:
            cart = models.Cart.objects.get(user=request.user)
            if not cart.items.exists():
                messages.error(request, "Your cart is empty.")
                return redirect("")
        except models.Cart.DoesNotExist:
            messages.error(request, "Your cart is empty.")
            return redirect("")
        
        if request.method == "POST":
            form = forms.CheckoutForm(request.POST)
            if form.is_valid():
                order = form.save(commit=False)
                order.user = request.user
                order.save()
                
                for item in cart.items.all():
                    models.OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        price=item.product.price,
                        quantity=item.quantity,
                    )
                
                cart.items.all().delete()
                request.session["order_id"] = order.id
                return redirect("")
        else:
            form = forms.CheckoutForm()
    return render(request, "", {"cart": cart, "form": form})


# Payment proccess
def payment_process(request):
    order_id = request.session.get("order_id")
    if not order_id:
        return redirect("")
    order = get_object_or_404(models.Order, id=order_id)
    payment_data = sslcommerz.generate_sslcommerz_payment(request,order)
    if payment_data["status"]=="SUCCESS":
        return redirect("")
    else:
        messages.error(request, "Payment getway error")


def payment_success(request, order_id):
    order = get_object_or_404(models.Order, id=order_id, user=request.user)
    order.paid = True
    order.status = 'Processing'
    order.transaction_id = order.id
    order.save()
    order_items = order.order_items.all()
    for item in order_items:
        product = item.product
        product.stock -= item.quantity
        if product.stock < 0:
            product.stock = 0   
        product.save()
    messages.success(request, "Your payment was successful. Thank you for your order!")
    return render(request, "", {"order": order})

def payment_fail(request, order_id):
    order = get_object_or_404(models.Order, id=order_id, user=request.user)
    order.status = 'Cancelled'
    order.save()
    messages.error(request, "Your payment failed. Please try again.")
    return render(request, "", {"order": order})

def payment_cancel(request, order_id):
    order = get_object_or_404(models.Order, id=order_id, user=request.user)
    order.status = 'Cancelled'
    order.save()
    messages.error(request, "Your payment was cancelled.")
    return render(request, "", {"order": order})