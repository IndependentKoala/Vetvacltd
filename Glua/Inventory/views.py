from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.db.models import Sum, F, Q
from .models import Drug, Sale, Stocked, LockedProduct
from .forms import DrugCreation
from django.contrib import messages
from django.views.generic import ListView, UpdateView
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.timezone import now
from datetime import datetime, timedelta, time
from django.db.models import Count
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.auth import logout
from django.core.paginator import Paginator


# Create your views here.

@login_required
def home(request):
    today = timezone.now().date()

    # Get the products expiring within the next 10 days
    expiring_soon = Drug.objects.filter(expiry_date__lte=today + timedelta(days=10), expiry_date__gt=today)

    # Get the products with stock below the reorder level
    low_stock = Drug.objects.filter(stock__lte=F('reorder_level'))

    # Pagination handling
    per_page = request.GET.get('per_page', 10)  # Default to 10 per page
    page_number = request.GET.get('page', 1)    # Get the current page number
    drugs = Drug.objects.all().order_by('name')# Get all drugs ordered by name

    # Create a paginator and get the page object for the current page
    paginator = Paginator(drugs, per_page)
    page_obj = paginator.get_page(page_number)

    # Check if the modal has already been shown in this session
    show_modal = not request.session.get('modal_shown', False)  # Only show modal if 'modal_shown' is not set or False

    if show_modal:
        print("Modal will be shown")
        request.session['modal_shown'] = True  # Set the session variable to True after showing the modal
        request.session.modified = True  # Ensure the session is saved
    else:
        print("Modal already shown in this session")
    
    # Pass these to the template
    context = {
        'drugs': page_obj,  # Pass the paginated drugs
        'expiring_soon': expiring_soon,
        'low_stock': low_stock,
        'show_modal': show_modal,  # Pass this flag to the template
    }

    return render(request, 'Inventory/home.html', context)



@login_required
def createDrug(request):
    try:
        if request.method == 'POST':
            form = DrugCreation(request.POST)
            if form.is_valid():
                name = form.cleaned_data.get('name')
                form.save()
                messages.success(
                    request, f'{name} has been successfully added to the inventory'
                )
                return redirect('home')  # Redirect to the homepage or another page
        else:
            form = DrugCreation()

        context = {'form': form}
        return render(request, 'Inventory/create.html', context)

    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('home')  # Redirect to 'home' in case of an error


@login_required
def addStock(request, pk):
    drug = Drug.objects.get(id=pk)
    supp = request.POST.get('supplier')
    amount_added = int(request.POST.get('added'))
    drug.stock += amount_added
    Stocked.objects.create(
        drug_name=drug, supplier=supp, staff=request.user, number_added=amount_added, total=drug.stock)
    drug.save()
    messages.success(request, f'{amount_added} {drug.name} added')
    return redirect('stocking')


class stockingListView(ListView):
    model = Drug
    context_object_name = 'drugs'
    paginate_by = 5
    template_name = 'Inventory/stock.html'
    ordering = ['name']


@login_required
def sellDrug(request, pk):
    if request.method == 'POST':
        quantity = float(request.POST.get('quantity'))
        client = request.POST.get('client')
        drug = get_object_or_404(Drug, pk=pk)
        
        if drug.stock >= quantity:
            # Update drug stock
            drug.stock -= quantity
            drug.save()
            
            # Create sale record
            Sale.objects.create(
                seller=request.user,
                drug_sold=drug,
                client=client,
                batch_no=drug.batch_no,
                quantity=quantity,
                remaining_quantity=drug.stock
            )
            
            messages.success(request, f'{quantity} {drug.name} sold to {client}')
        else:
            messages.error(request, 'Not enough stock available')
            
        return redirect('home')

@login_required
def lockDrug(request, pk):
    if request.method == 'POST':
        quantity = float(request.POST.get('quantity'))
        client = request.POST.get('client')
        drug = get_object_or_404(Drug, pk=pk)
        
        if drug.stock >= quantity:
            # Lock product by creating a LockedProduct record
            LockedProduct.objects.create(
                drug=drug,
                locked_by=request.user,
                quantity=quantity,
                client=client
            )
            
            drug.stock -= quantity
            drug.save()

            last_sale = Sale.objects.filter(drug_sold=drug).order_by('-date_sold').first()

    # If a sale exists, add the locked quantity to the remaining_quantity
            if last_sale:
                if last_sale.remaining_quantity is None:
                    last_sale.remaining_quantity = 0  # Ensure it's initialized
                last_sale.remaining_quantity = drug.stock
                last_sale.save()  
            
            # Reduce stock
            
            messages.success(request, f'{quantity} {drug.name} locked.')
        else:
            messages.error(request, 'Not enough stock to lock')
        
        return redirect('home')


def search(request):
    drugs = Drug.objects.all().order_by('name')
    query = request.POST.get('q')

    if query:
        drugs = Drug.objects.filter(
            Q(name__icontains=query) | Q(batch_no__icontains=query))

    context = {'drugs': drugs}
    return render(request, 'Inventory/home.html', context)


def binsearch(request):
    bins = Sale.objects.all().order_by('drug_sold__name')
    query = request.POST.get('quiz')

    print("Search Query:", query)  # Debugging the query received

    if query:
        bins = Sale.objects.filter(
            Q(client__icontains=query) |
            Q(drug_sold__name__icontains=query) |
            Q(drug_sold__batch_no__icontains=query)
        )

    context = {'sales': bins}
    return render(request, 'Inventory/bin.html', context)


def searchstock(request):
    drugs = Drug.objects.all().order_by('name')
    query = request.POST.get('s')

    if query:
        drugs = Drug.objects.filter(Q(name__icontains=query))

    context = {'drugs': drugs}
    return render(request, 'Inventory/stock.html', context)


def salehistory(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        sales = Sale.objects.filter(
            date_sold__range=[start_date, end_date]).order_by('-date_sold')
        if sales:
            total_sales = sales.aggregate(
                total=Sum(F('quantity') * F('sale_price')))['total']
            bought_at = sales.aggregate(
                total=Sum(F('quantity') * F('buying_price')))['total']
            profit = total_sales - bought_at
            context = {'sales': sales, 'profit': profit, 'total_sales': total_sales}
        else:
            messages.success(
                request, 'Sorry no sales were done within those dates')
            context = {}
            return redirect('history')
    else:
        context = {}
    return render(request, 'Inventory/history.html', context)


def todaysales(request):
    today = datetime.now().date()
    tomorrow = today + timedelta(1)
    start_date = datetime.combine(today, time())
    end_date = datetime.combine(tomorrow, time())

    if start_date and end_date:
        sales = Sale.objects.filter(
            date_sold__range=[start_date, end_date]).order_by('-date_sold')
        if sales:
            total_sales = sales.aggregate(
                total=Sum(F('quantity') * F('sale_price')))['total']
            bought_at = sales.aggregate(
                total=Sum(F('quantity') * F('buying_price')))['total']
            profit = total_sales - bought_at
            context = {'sales': sales, 'profit': profit, 'total_sales': total_sales}
        else:
            messages.success(request, 'Sorry no sales were done today')
            context = {}
            return redirect('history')
    else:
        context = {}
    return render(request, 'Inventory/today.html', context)


def StockAdded(request):
    start_date = request.GET.get('date_start')
    end_date = request.GET.get('date_end')
    if start_date and end_date:
        glua_stocked_days = Stocked.objects.filter(
            date_added__range=[start_date, end_date]).order_by('-date_added')
        context = {'stocked': glua_stocked_days}
    else:
        context = {}

    return render(request, 'Inventory/stocked.html', context)


class modifyDrugUpdateView(UpdateView):
    template_name = 'Inventory/create.html'
    model = Drug
    fields = ['name', 'stock', 'batch_no']
    success_url = "/"


def bin_report(request):
    sales = Sale.objects.all().order_by('-date_sold')
    
    # return render(request, 'Inventory/bin.html', {'sales': sales})
    sales = Sale.objects.all().order_by('-date_sold')  # Replace with your queryset
    per_page = int(request.GET.get('per_page', 10))  # Default to 10 items per page
    paginator = Paginator(sales, per_page)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    return render(request, 'Inventory/bin.html', {'sales': page_obj})

@login_required
def dashboard(request):
    today = timezone.now().date()

    # Get the expired products (expiry date is in the past)
    expired_drugs = Drug.objects.filter(expiry_date__lt=today)

    # Get the products expiring within the next 10 days
    expiring_soon = Drug.objects.filter(expiry_date__lte=today + timedelta(days=10), expiry_date__gt=today)

    # Get the products with stock below the reorder level
    low_stock = Drug.objects.filter(stock__lte=F('reorder_level'))

    # Check if the modal has already been shown in this session
    show_modal = not request.session.get('modal_shown', False)  # Only show modal if 'modal_shown' is not set or False

    if show_modal:
        request.session['modal_shown'] = True  # Set the session variable to True after showing the modal
        request.session.modified = True  # Ensure the session is saved
    
    # Summary Data
    total_products = Drug.objects.count()
    low_stock_products = Drug.objects.filter(stock__lte=F('reorder_level')).count()
    out_of_stock_products = Drug.objects.filter(stock=0).count()
    zero_stock_products = Drug.objects.filter(stock__lte=5).count()
    locked_products = LockedProduct.objects.all().count()

    # Top Sold Products
    top_sold_products = (
        Sale.objects.values("drug_sold__name")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("-total_quantity")[:5]
    )

    # Calculate the total count of expired and expiring soon drugs
    total_expiring_count = expired_drugs.count() + expiring_soon.count()

    context = {
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'zero_stock_products': zero_stock_products,
        'top_sold_products': top_sold_products,
        'expired_drugs_count': expired_drugs.count(),  # Add the count of expired drugs
        'expiring_soon_count': expiring_soon.count(),  # Add the count of expiring soon drugs
        'total_expiring_count': total_expiring_count,  # Add the total count of expired and expiring soon drugs
        'expired_drugs': expired_drugs,  # Pass expired drugs to the template
        'expiring_soon': expiring_soon,  # Pass expiring soon drugs to the template
        'low_stock': low_stock,
        'show_modal': show_modal, 
        'locked_products': locked_products,
    }
    return render(request, 'Inventory/dashboard.html', context)

@login_required
def low_stock_view(request):
    # Get the products with stock below or equal to the reorder level
    low_stock = Drug.objects.filter(stock__lte=F('reorder_level'))

    context = {
        'low_stock': low_stock
    }

    return render(request, 'Inventory/lowstock.html', context)

def get_online_offline_users(request):
    # Get all users
    all_users = User.objects.all()
    
    # Split them into online and offline users
    online_users = [user.username for user in all_users if user.is_active]  # Assuming 'is_active' indicates online status
    offline_users = [user.username for user in all_users if not user.is_active]  # Assuming 'is_active' indicates offline status

    # Return as JSON response
    return JsonResponse({
        'online_users': online_users,
        'offline_users': offline_users,
    })

@login_required
def locked_products(request):
    """
    Display the list of locked products in ascending order by the drug name.
    """
    # Fetch all locked products and order by the drug's name
    locked_products = LockedProduct.objects.all().order_by('drug__name')
    return render(request, 'Inventory/locked.html', {'locked_products': locked_products})

@login_required
def post_locked_product(request, lock_id):
    """
    Handle the action of posting a locked product.
    """
    lock = get_object_or_404(LockedProduct, id=lock_id)
    if request.method == 'POST':
        quantity = lock.quantity
        client = lock.client  # Assuming 'locked_by' is a User and you need their username as the client.
        drug = lock.drug
        
        # Create sale record
        Sale.objects.create(
            seller=request.user,
            drug_sold=drug,
            client=client,
            batch_no=drug.batch_no,
            sale_price=drug.selling_price,
            quantity=quantity,
            remaining_quantity=drug.stock
        )

        # Delete the locked product
        lock.delete()

        # Display a success message
        messages.success(request, f'{quantity} {drug.name} sold to {client} and lock removed.')
       
        # Redirect to the locked products page
        return redirect('locked_products')


@login_required
def unlock_product(request, lock_id):
    """
    Handle the action of unlocking a product.
    """
    # Fetch the locked product instance
    lock = get_object_or_404(LockedProduct, id=lock_id)

    # Add the locked quantity back to the drug's stock
    drug = lock.drug
    if lock.quantity:  # Ensure the quantity is not None or empty
        drug.stock += int(lock.quantity)  # Adding the locked quantity back to the stock
        drug.save()  # Save the updated stock to the database

    # Fetch the last sale entry for this drug
    last_sale = Sale.objects.filter(drug_sold=drug).order_by('-date_sold').first()

    # If a sale exists, add the locked quantity to the remaining_quantity
    if last_sale:
        if last_sale.remaining_quantity is None:
            last_sale.remaining_quantity = 0  # Ensure it's initialized
        last_sale.remaining_quantity = drug.stock
        last_sale.save()  # Save the updated remaining quantity

    # Delete the locked product after updating the stock and sales
    lock.delete()

    # Redirect to the locked products page
    messages.success(request, f"{lock.quantity} {drug.name} unlocked and added back to stock.")
    return redirect('locked_products')


@login_required
def locked_search(request):
    query = request.POST.get('quiz', '')  # Retrieve the search query from the form
    locked_products = LockedProduct.objects.filter(
        Q(drug__name__icontains=query) | Q(locked_by__username__icontains=query)
    )  # Search for drug name or locked_by username containing the query (case-insensitive)

    return render(request, 'Inventory/locked.html', {'locked_products': locked_products})

def user_management(request):
    """
    Display the user management page with a form to add new users
    and a list of online/offline users.
    """
    # Get all users
    users = User.objects.all()

    # Check for online users
    sessions = Session.objects.filter(expire_date__gte=now())
    online_user_ids = [session.get_decoded().get('_auth_user_id') for session in sessions]

    # Annotate users with their online/offline status
    for user in users:
        user.is_online = str(user.id) in online_user_ids

    context = {
        'users': users,
    }
    return render(request, 'Inventory/user_management.html', context)


def add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        # Validate inputs
        if not username or not email or not password:
            messages.error(request, "All fields are required.")
            return render(request, 'add_user.html')  # Ensure form is empty if error

        if User.objects.filter(Q(username=username) | Q(email=email)).exists():
            messages.error(request, "A user with this username or email already exists.")
            return render(request, 'add_user.html')  # Ensure form is empty if error

        User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, "New user added successfully.")
        return redirect('user_management')  # Redirect to a success page

    # If the request method is not POST, render the page with an empty form
    return render(request, 'add_user.html')  # Ensure form is empty when not submitting

def user_logout(request):
    # Clear the session variable so that the modal shows again after logging in
    if 'modal_shown' in request.session:
        del request.session['modal_shown']
    logout(request)
    return HttpResponseRedirect('/login')  # Redirect to login page or home page

def out_of_stock(request):
    out_of_stock_products = Drug.objects.filter(stock=0)
    return render(request, 'Inventory/out_of_stock.html', {'out_of_stock': out_of_stock_products})

def expiring_soon(request):
    today = timezone.now().date()
    expiring_products = Drug.objects.filter(expiry_date__lte=today + timedelta(days=10))
    return render(request, 'Inventory/expiring_soon.html', {'expiring_soon': expiring_products})

blue_shades = [
    {"hex": "#0047AB", "rgba": "rgba(0, 71, 171, 1)"},
    {"hex": "#007b83", "rgba": "rgba(0, 123, 131, 1)"},
    {"hex": "#0275d8", "rgba": "rgba(2, 117, 216, 1)"},
    {"hex": "#4682b4", "rgba": "rgba(70, 130, 180, 1)"},
    {"hex": "#5f9ea0", "rgba": "rgba(95, 158, 160, 1)"},
    {"hex": "#006994", "rgba": "rgba(0, 105, 148, 1)"},
]

other_colors = [
    {"hex": "#fbe7e4", "rgba": "rgba(251, 231, 228, 1)"},
    {"hex": "#e8f8f5", "rgba": "rgba(232, 248, 245, 1)"},
    {"hex": "#fff5e6", "rgba": "rgba(255, 245, 230, 1)"},
    {"hex": "#f9e6ff", "rgba": "rgba(249, 230, 255, 1)"},
    {"hex": "#fff9e6", "rgba": "rgba(255, 249, 230, 1)"},
    {"hex": "#ffebf0", "rgba": "rgba(255, 235, 240, 1)"},
]

def show_colors(request):
    context = {
        'blue_colors': blue_shades,
        'other_colors': other_colors
    }
    return render(request, 'Inventory/colors.html', context)