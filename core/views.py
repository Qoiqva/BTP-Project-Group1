from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect
from django.utils import timezone
from .models import Item, OrderItem, Order, Address, Payment, UserProfile, Promotion
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
import uuid
from decimal import Decimal
from .forms import UserForm, ProfileForm, RescheduleForm, UserProfileForm
from django.db.models import Q
from .models import LABEL_CHOICES
from .models import CATEGORY_CHOICES


def checkout(request):
    return render(request, "checkout.html")

def productlist(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "product-page.html", context)

class HomeView(ListView):
    model = Item 
    template_name = "home-page.html"
    context_object_name = "object_list"
    
    def get_queryset(self):
        query = self.request.GET.get("q")
        sort = self.request.GET.get("sort")
        category = self.request.GET.getlist("category")
        labels = self.request.GET.getlist("labels")


        qs = Item.objects.all()

        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )

        if category:
            qs = qs.filter(category__in=category)

        if labels:
            qs = qs.filter(labels__in=labels)

        if sort == "price-asc":
            qs = qs.order_by("price")
        elif sort == "price-desc":
            qs = qs.order_by("-price")

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Fetch all unique categories from Item
        category_dict = dict(CATEGORY_CHOICES)
        category_keys = Item.objects.values_list("category", flat=True).distinct()
        context["categories"] = [(key, category_dict.get(key, key)) for key in category_keys]

        # Fetch all unique labels from Item
        label_dict = dict(LABEL_CHOICES)
        label_keys = Item.objects.values_list("labels", flat=True).distinct()
        context["labels"] = [(key, label_dict.get(key, key)) for key in label_keys]

        return context


    def dispatch(self, request, *args, **kwargs):
        print(f"User auth status on home: {request.user.is_authenticated}")
        if request.user.is_authenticated and request.user.is_superuser:
            from django.contrib.auth import logout
            logout(request)
        return super().dispatch(request, *args, **kwargs)

class CheckOutView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        order = Order.objects.filter(user=self.request.user, is_ordered=False).first()

        if order:
            discount_data = order.calculate_discounts()

            context = {
                'order': order,
                'object': order,
                **discount_data  
            }
            return render(self.request, 'checkout.html', context)

        messages.warning(self.request, "Nothing to checkout!")
        return redirect("core:home")

    def post(self, *args, **kwargs):
        order = Order.objects.filter(user=self.request.user, is_ordered=False).first()
        if not order:
            messages.error(self.request, "No active order found")
            return redirect("core:checkout")

        address = Address.objects.create(
            user=self.request.user,
            address1=self.request.POST.get('address1'),
            address2=self.request.POST.get('address2'),
            country=self.request.POST.get('country'),
            state=self.request.POST.get('state'),
            zip_code=self.request.POST.get('zip_code'),
            delivery_instructions=self.request.POST.get('delivery_instructions')
        )

        payment = Payment.objects.create(
            user=self.request.user,
            payment_type=self.request.POST.get('payment_type'),
            name_on_card=self.request.POST.get('name_on_card'),
            card_number=self.request.POST.get('card_number'),
            expiration=self.request.POST.get('expiration'),
            cvv=self.request.POST.get('cvv')
        )

        discount_data = order.calculate_discounts()

        order.address = address
        order.payment = payment
        order.delivery_date = self.request.POST.get('delivery_date')
        order.delivery_timeslot = self.request.POST.get('delivery_timeslot')
        order.discount_amount = discount_data['total_discount']
        order.final_price = order.get_final_price()
        order.is_ordered = True
        order.status = 'Pending'
        order.ordered_date = timezone.now()
        order.save()

        messages.success(self.request, "Order placed successfully!")
        return redirect("core:order-history")


class ItemDetailView(DetailView):
    model = Item
    template_name = "product-page.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        item = context['object']
        discounted_price, discount_rate = item.get_discounted_price()
        context['has_promotions'] = discounted_price is not None
        context['discounted_price'] = discounted_price
        context['discount_rate'] = discount_rate
        return context

class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        order = Order.objects.filter(user=self.request.user, is_ordered=False).first()

        if order:
            print(order)
            print("Order items:", order.items.all())
            context = {'object': order}
            print(context["object"])
            return render(self.request, 'order-summary.html', context)
        
        # Enhanced messaging for better clarity
        messages.warning(self.request, "Your cart is empty. Start adding fresh produce!")
        return redirect("core:home")

class OrderHistoryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        orders = Order.objects.filter(
            user=self.request.user, 
            is_ordered=True
        ).order_by('-ordered_date')  # Newest first
        
        if orders:
            context = {'orders': orders}
            return render(self.request, 'order-history.html', context)
        
        messages.warning(self.request, "Your order history is empty.")
        return redirect("core:home")

class OrderDetailView(LoginRequiredMixin, View):
    def get(self, request, slug, *args, **kwargs):
        order = get_object_or_404(Order, slug=slug, user=request.user, is_ordered=True)
        context = {'object': order}
        return render(request, 'order-detail.html', context)


class RescheduleOrderView(LoginRequiredMixin, View):
    def get(self, request, slug):
        order = get_object_or_404(Order, slug=slug, user=request.user)

        if order.status != 'Pending':
            return redirect('core:order-detail', slug=order.slug)
        
        form = RescheduleForm(instance=order)

        return render(request, 'reschedule-order.html', {'form': form, 'order': order})
    def post(self, request, slug):
        order = get_object_or_404(Order, slug=slug, user=request.user)

        if order.status != 'Pending':
            return redirect('core:order-detail', slug=order.slug)
        
        form = RescheduleForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, "Delivery successfully rescheduled!")
            return redirect('core:order-detail', slug=order.slug)
        messages.error(request, "Please correct the error below.")
        return render(request, 'reschedule-order.html', {'form': form, 'order': order})
    

class PromotionsView( View):
    def get(self, request):
        active_promotions = Promotion.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).order_by('end_date')
        
        return render(request, 'promotions.html', {'promotions': active_promotions})
    

@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    
    # Get or create cart for current user
    order = Order.get_or_create_cart(request.user)
    print(f"[DEBUG] Order retrieved or created - ID: {order.id}, User: {order.user.username}, Existing items count: {order.items.count()}")

    # Filter for existing OrderItem in this cart
    order_items = order.items.filter(item=item, user=request.user, ordered=False, order_id = order.id)
    print(f"[DEBUG] Matching OrderItem(s) in current cart: {order_items}")

    if order_items.exists():
        order_item = order_items.first()
        print(f"[DEBUG] OrderItem exists - Current quantity: {order_item.quantity}")
        order_item.quantity += 1
        order_item.save()
        print(f"[DEBUG] Updated quantity: {order_item.quantity}")
        messages.info(request, f"{item.name} were added to your cart (Total: {order_item.quantity} left).")
    else:
        order_item = OrderItem.objects.create(item=item, user=request.user, quantity=1, ordered=False, order_id = order.id)
        print(f"[DEBUG] New OrderItem created - ID: {order_item.id}, Quantity: {order_item.quantity}")
        order.items.add(order_item)
        order.save()
        print(f"[DEBUG] OrderItem added to Order ID: {order.id}. Total items now: {order.items.count()}")
        messages.info(request, f"{item.name} added to your cart.")
    
    print(f"[DEBUG] Redirecting to order summary...")
    return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)

    try:
        order = Order.objects.get(user=request.user, is_ordered=False)
    except Order.DoesNotExist:
        messages.info(request, "You do not have an active order.")
        return redirect("core:product", slug=slug)

    
    order_items = OrderItem.objects.filter(item=item, user=request.user, ordered=False)

    if order_items.exists():
        for order_item in order_items:
           
            order.items.remove(order_item)
            order_item.delete() 

        messages.info(request, f"All {item.name} items have been removed from your cart.")

        if order.items.count() == 0:
            order.delete()
            
    else:
        messages.info(request, f"{item.name} is not in your cart.")

    return redirect("core:order-summary")





@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order = Order.objects.filter(user=request.user, is_ordered=False).first()

    if order:
        # Check if the item is already in the cart
        order_item = order.items.filter(item=item, user=request.user, ordered=False).first()

        if order_item:
            if order_item.quantity > 1:
                # Decrease the quantity by 1
                order_item.quantity -= 1
                order_item.save()
                messages.info(request, f"The quantity of {item.name} has been updated.")
            else:
                # Remove the item completely from the cart
                order.items.remove(order_item)
                order_item.delete()
                messages.info(request, f"{item.name} has been removed from your cart.")
            
        else:
            # Item is not in the cart
            messages.info(request, f"{item.name} is not in your cart.")
            
    else:
        # No active order
        messages.info(request, "You do not have an active order.")
    return redirect("core:order-summary")


@login_required
def account_view(request):
    if not hasattr(request.user, 'userprofile'):
        UserProfile.objects.create(user=request.user)

    edit_mode = request.GET.get("edit") == "true"

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(request.POST, instance=request.user.userprofile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('core:account')  
        else:
            edit_mode = True
    else:
        user_form = UserForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.userprofile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'edit_mode': edit_mode,
    }
    return render(request, 'account.html', context)


@login_required
def complete_profile(request):
    # If profile exists, don't show this page again
    if hasattr(request.user, 'userprofile'):
        return redirect('core:home')

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        user_form.fields.pop('email')  

        profile_form = UserProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()  
            profile = profile_form.save(commit=False)
            profile.user = user  
            profile.save()
            return redirect('core:account')  
    else:
        user_form = UserForm(instance=request.user)
        user_form.fields.pop('email')  
        profile_form = UserProfileForm()

    return render(request, 'account/complete_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })