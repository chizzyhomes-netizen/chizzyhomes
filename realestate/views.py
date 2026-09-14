from django.shortcuts import render
from django.contrib.auth import views as auth_views
# Create your views here.
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from .models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.db.models import Q
from .models import Property,PropertyLocation
from django.contrib.auth.views import LogoutView

def home(request):
    return render(request, "index.html")

def signup(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        phone_number = request.POST.get("phone_number", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        agent_access_code = request.POST.get("agent_access_code", "").strip()

        # Basic validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("signup")

        # Default role
        role = "customer"

        # Check agent secret
        if agent_access_code:
            if agent_access_code == settings.AGENT_ACCESS_CODE:
                role = "agent"
            else:
                messages.error(request, "Invalid agent access code.")
                return redirect("signup")

        # Create account
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            phone_number=phone_number,
            role=role
        )

        # Log the user in immediately
        login(request, user)

        if role == "agent":
            return redirect("agent_dashboard")

        return redirect("homes")

    return render(request, "signup.html")

def signin(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            # Send agents to their dashboard
            if user.role == "agent":
                return redirect("agent_dashboard")

            # Send normal users to homepage
            return redirect("homes")

        messages.error(request, "Invalid username or password.")

    return render(request, "signin.html")


def signout(request):
    logout(request)
    return redirect("home")

@login_required
def agent_dashboard(request):

    # Only agents can access this dashboard
    if request.user.role != "agent":
        return HttpResponseForbidden(
            "You do not have permission to access the agent dashboard."
        )

    properties = Property.objects.filter(
        agent=request.user
    )

    total_properties = properties.count()

    available_properties = properties.filter(
        status="available"
    ).count()

    rented_properties = properties.filter(
        status="rented"
    ).count()
    active_users = User.objects.all()  # Or User.objects.filter(is_active=True)
    total_users = active_users.count()
    context = {
        "properties": properties,
        "total_properties": total_properties,
        "available_properties": available_properties,
        "rented_properties": rented_properties,
        'active_users': active_users,
        'total_users': total_users,
    }

    return render(
        request,
        "dashboard.html",
        context
    )


from django.contrib import messages
from .models import Property, PropertyImage, PropertyVideo


@login_required
def add_property(request):

    # Only agents can list properties
    if request.user.role != "agent":
        return HttpResponseForbidden("Only agents can list properties.")

    if request.method == "POST":

        # 1. Create the Property instance
        property_obj = Property.objects.create(
            agent=request.user,
            title=request.POST.get("title", "").strip(),
            property_type=request.POST.get("property_type"),
            description=request.POST.get("description", "").strip(),
            price=request.POST.get("price"),
            location=request.POST.get("location", "Gidan Kwano, Minna").strip(),
            address=request.POST.get("address", "").strip(),
            bedrooms=request.POST.get("bedrooms", 1),
            bathrooms=request.POST.get("bathrooms", 1),
            status=request.POST.get("status", "available"),
            phone_number=request.POST.get("phone_number", "").strip(),
            link=request.POST.get("link", "").strip(),

            # Amenities
            starlink="starlink" in request.POST,
            private_transformer="private_transformer" in request.POST,
            water="water" in request.POST,
            generator="generator" in request.POST,
            solar_power="solar_power" in request.POST,
            security="security" in request.POST,
            parking="parking" in request.POST,
            furnished="furnished" in request.POST,
            air_conditioning="air_conditioning" in request.POST,
            water_heater="water_heater" in request.POST,
            kitchen="kitchen" in request.POST,
            borehole="borehole" in request.POST,
            network_coverage="network_coverage" in request.POST,
        )

        # 2. Create the PropertyLocation record linked to Property
        lat = request.POST.get("latitude")
        lng = request.POST.get("longitude")

        if lat and lng:
            PropertyLocation.objects.create(
                property=property_obj,
                zone=request.POST.get("zone", "gk_main_gate"),
                latitude=float(lat),
                longitude=float(lng),
                landmark=request.POST.get("landmark", "").strip(),
            )

        # 3. Handle Image Uploads (Up to 4 images)
        images = request.FILES.getlist("images")
        for img in images[:4]:
            PropertyImage.objects.create(
                property=property_obj,
                image=img
            )

        # 4. Handle Video Upload (1 video)
        video_file = request.FILES.get("video")
        if video_file:
            PropertyVideo.objects.create(
                property=property_obj,
                video=video_file
            )

        messages.success(request, "Your property has been listed successfully!")
        return redirect("agent_dashboard")

    return render(request, "add_property.html")


from django.core.paginator import Paginator
import json
from django.shortcuts import render
from .models import Property, PropertyLocation

def property_list_view(request):
    selected_zone = request.GET.get('zone', '').strip()
    selected_type = request.GET.get('type', '').strip()
    query = request.GET.get('q', '').strip()

    # Base queryset
    properties = Property.objects.filter(status="available").order_by('-created_at')

    # Apply Zone filter matching model choices/prefixes
    if selected_zone:
        if selected_zone in ['gk_main_gate', 'gk_express_south_west', 'gk_market_hub', 'gk_residential_west',
                             'gk_residential_east', 'gk_express_south_south', 'gk_express_south', 'gk_express_north',
                             'dama_north', 'dama_central', 'dama_south', 'gm_main_road', 'gm_interior', 'gm_east']:
            properties = properties.filter(location_details__zone=selected_zone)
        elif selected_zone == 'gidan_kwano':
            properties = properties.filter(location_details__zone__startswith='gk_')
        elif selected_zone == 'dama':
            properties = properties.filter(location_details__zone__startswith='dama_')
        elif selected_zone == 'gidan_mangoro':
            properties = properties.filter(location_details__zone__startswith='gm_')

    # Apply Property Type filter matching model choices exactly
    if selected_type:
        properties = properties.filter(property_type=selected_type)

    if query:
        properties = properties.filter(title__icontains=query)

    # Pagination: 9 properties per page
    paginator = Paginator(properties, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Format property data for Leaflet map markers
    map_data = []
    for p in properties:
        if hasattr(p, 'location_details') and p.location_details and p.location_details.latitude and p.location_details.longitude:
            first_img = p.images.first()
            map_data.append({
                "id": p.id,
                "title": p.title,
                "type": p.get_property_type_display(),
                "price": f"₦{p.price:,.0f}",
                "lat": float(p.location_details.latitude),
                "lng": float(p.location_details.longitude),
                "zone": p.location_details.get_zone_display(),
                "landmark": p.location_details.landmark,
                "image": first_img.image.url if first_img else "",
                "url": f"/properties/{p.id}/",
            })

    context = {
        "page_obj": page_obj,
        "map_data_json": json.dumps(map_data),
        "selected_zone": selected_zone,
        "selected_type": selected_type,
        "query": query,
        "total_results": properties.count(),
        "zone_choices": PropertyLocation.ZONE_CHOICES,
        "property_types": Property.PROPERTY_TYPES,
    }
    return render(request, "property_list.html", context)

from django.shortcuts import render
from django.core.paginator import Paginator
from .models import Property


def home_view(request):
    """Homepage: Light preview grid + Map markers"""
    all_properties = Property.objects.all()
    featured_properties = Property.objects.order_by('-created_at')[:8]

    context = {
        'all_properties': all_properties,
        'featured_properties': featured_properties,
    }
    return render(request, 'home.html', context)


def property_list_view(request):
    """Search & Browse Page: Displays all filtered properties with pagination"""
    properties = Property.objects.all().order_by('-created_at')

    # Get Filter Parameters from URL query params
    # Read Search Parameters
    query = request.GET.get('q', '').strip()
    zone = request.GET.get('zone', '')
    property_type = request.GET.get('property_type', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')

    # 1. Full-text / Phrase Query Filter (Safely handling words/hyphens)
    if query:
        keywords = query.split()
        for word in keywords:
            # Removed the bare zone__icontains check that is causing the FieldError
            word_q = (
                    Q(title__icontains=word) |
                    Q(description__icontains=word) |
                    Q(address__icontains=word)
            )

            # Use only relational lookups for zone data
            try:
                word_q |= Q(location_details__zone__icontains=word) | Q(location_details__landmark__icontains=word)
            except Exception:
                pass

            properties = properties.filter(word_q)

    # Apply Filters dynamically
    if zone:
        properties = properties.filter(location_details__zone=zone)
    if property_type:
        properties = properties.filter(property_type=property_type)

    if min_price:
        try:
            properties = properties.filter(price__gte=float(min_price))
        except ValueError:
            pass

    if max_price:
        try:
            properties = properties.filter(price__lte=float(max_price))
        except ValueError:
            pass

    # Paginate results (12 properties per page)
    paginator = Paginator(properties, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_results': properties.count(),
        'query': query,
        'selected_zone': zone,
        'selected_type': property_type,
        'selected_min_price': min_price,
        'selected_max_price': max_price,
    }
    return render(request, 'property_list.html', context)

from django.shortcuts import render
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Property

def search_hub_view(request):
    """Dedicated Search Hub with Multi-Word Keyword + Description Search"""
    properties = Property.objects.all().order_by('-created_at')

    # Read Search Parameters
    query = request.GET.get('q', '').strip()
    zone = request.GET.get('location', '') or request.GET.get('zone', '')
    property_type = request.GET.get('property_type', '')
    max_price = request.GET.get('max_price', '')

    # 1. Full-text / Multi-word Search
    if query:
        words = query.split()
        word_queries = Q()
        for word in words:
            word_queries |= Q(title__icontains=word)
            word_queries |= Q(description__icontains=word)
            word_queries |= Q(address__icontains=word)
            # Traverse OneToOne relation to actual text/choice fields on PropertyLocation
            word_queries |= Q(location_details__zone__icontains=word)
            word_queries |= Q(location_details__landmark__icontains=word)

        properties = properties.filter(word_queries).distinct()

    # 2. Categorical Zone Filter
    if zone:
        properties = properties.filter(location_details__zone=zone)

    # 3. Categorical Type & Price Filters
    if property_type:
        properties = properties.filter(property_type=property_type)
    if max_price:
        properties = properties.filter(price__lte=max_price)

    # 4. Pagination
    paginator = Paginator(properties, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'total_results': properties.count(),
        'query': query,
        'selected_zone': zone,
        'selected_type': property_type,
        'selected_price': max_price,
    }
    return render(request, 'search.html', context)


from django.shortcuts import render, get_object_or_404
from .models import Property


def property_detail(request, pk):
    # Retrieve property or return 404 if not found
    property_obj = get_object_or_404(
        Property.objects.prefetch_related('images').select_related('location_details'),
        pk=pk
    )

    # Safely get zone only if location_details exists
    zone_value = None
    if hasattr(property_obj, 'location_details') and property_obj.location_details:
        zone_value = property_obj.location_details.zone

    # Retrieve similar properties in the same zone if available
    similar_properties = []
    if zone_value:
        similar_properties = Property.objects.filter(
            location_details__zone=zone_value
        ).exclude(pk=property_obj.pk)[:3]

    context = {
        'property': property_obj,
        'similar_properties': similar_properties,
    }
    return render(request, 'property_detail.html', context)

def terms_view(request):
    return render(request, 'term.html')

def privacy_view(request):
    return render(request, 'privacy.html')

def about_view(request):
    return render(request, 'about.html')

def contact_view(request):
    return render(request, 'contact.html')


@login_required
def toggle_property_status(request, pk):
    property_item = get_object_or_404(Property, pk=pk, agent=request.user)

    # Toggle logic supporting boolean or string status choices
    if property_item.status == "available" or property_item.status == True or property_item.status == "Available":
        property_item.status = "rented"  # or False depending on your model field definition
    else:
        property_item.status = "available"  # or True

    property_item.save()
    return redirect('agent_dashboard')  # Update with your actual dashboard URL name if different


@login_required
def delete_property(request, pk):
    property_item = get_object_or_404(Property, pk=pk, agent=request.user)
    if request.method == "POST":
        property_item.delete()
    return redirect('agent_dashboard')
