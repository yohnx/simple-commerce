from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import User, Category, Listing, Comment, Bid

def listing(request, id):
    listing_details = Listing.objects.get(pk=id)
    isListingInWatchList = request.user in listing_details.watchList.all()
    allComments = Comment.objects.filter(listing = listing_details)
    isOwner = listing_details.owner.username == request.user.username
    return render(request, "auctions/listing.html", {
        "listings": listing_details,
        "isListingInWatchList": isListingInWatchList,
        "allComments": allComments,
        "isOwner": isOwner
    })

def closeAuction(request, id):
    listingData = Listing.objects.get(pk=id)
    isListingInWatchList = request.user in listingData.watchList.all()
    allComments = Comment.objects.filter(listing = listingData)
    isOwner = listingData.owner.username == request.user.username
    listingData.isActive = False
    listingData.save()
    return render(request, "auctions/listing.html", {
        "listings": listingData,
        "isListingInWatchList": isListingInWatchList,
        "allComments": allComments,
        "isOwner": isOwner,
        "updated": True,
        "message": "Congratulations ur Auction is Closed"
    })

def displayWatchList(request):
    current_user = request.user
    listings = current_user.listingWatchList.all()
    return render(request, "auctions/watchList.html", {
        "listings": listings
    })

def addComment(request, id):
    current_user = request.user
    listingData = Listing.objects.get(pk=id)
    message = request.POST["comment"]
    newComment = Comment(
        author = current_user,
        listing = listingData,
        message = message
    )
    newComment.save()
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def removeWatchList(request, id):
    listingData = Listing.objects.get(pk=id)
    current_user = request.user
    listingData.watchList.remove(current_user)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def addWatchList(request, id):
    listingData = Listing.objects.get(pk=id)
    current_user = request.user
    listingData.watchList.add(current_user)
    return HttpResponseRedirect(reverse("listing", args=(id, )))

def index(request):
    active_listing = Listing.objects.filter(isActive = True)
    all_categories = Category.objects.all()
    return render(request, "auctions/index.html", {
        "listings": active_listing,
        "categories": all_categories
    })

def displayCategory(request):
    if request.method == "POST":
        categoryFromForm = request.POST["category"]
        category = Category.objects.get(categoryName = categoryFromForm)
        active_listing = Listing.objects.filter(isActive = True, category = category)
        all_categories = Category.objects.all()
        return render(request, "auctions/index.html", {
            "listings": active_listing,
            "categories": all_categories
        })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")

def Create_listing(request):
    if request.method == "GET":
        all_categories = Category.objects.all()
        return render(request, "auctions/create.html", {
            "categories": all_categories
        })
    else:
        title = request.POST["title"]
        description = request.POST["description"]
        image_url = request.POST["image_url"]
        category = request.POST["category"]
        price = request.POST["price"]
        current_user = request.user
        new_category = Category.objects.get(categoryName = category)
        bid = Bid(
            bid=int(price),
            user = current_user
            )
        bid.save()
        new_listing = Listing(
            title = title,
            description = description,
            imageUrl = image_url,
            category = new_category,
            price = bid,
            owner = current_user
        )
        new_listing.save()
        return HttpResponseRedirect(reverse("index"))

def addBid(request, id):
    listingData = Listing.objects.get(pk=id)
    isListingInWatchList = request.user in listingData.watchList.all()
    allComments = Comment.objects.filter(listing = listingData)
    isOwner = listingData.owner.username == request.user.username
    newBid = request.POST["bid"]
    if int(newBid) > listingData.price.bid:
        updatedBid = Bid(user=request.user, bid=int(newBid))
        updatedBid.save()
        listingData.price = updatedBid
        listingData.save()
        return render(request, "auctions/listing.html", {
            "listings": listingData,
            "message": "Bid purchased successfully!",
            "updated": True,
            "isListingInWatchList": isListingInWatchList,
            "allComments": allComments,
            "isOwner": isOwner
        })
    else:
        return render(request, "auctions/listing.html", {
            "listings": listingData,
            "message": "Unable to purchase Bid!",
            "updated": False,
            "isOwner": isOwner
        })

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")
