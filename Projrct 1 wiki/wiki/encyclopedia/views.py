from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.urls import reverse
from . import util


def index(request):
    return render(request, "encyclopedia/index.html", {
        "entries": util.list_entries()
    })

def entry(request, title):
    content = util.get_entry(title)
    if content is None:
        return render(request, "encyclopedia/error.html", {
            "message": "Page not found"
        })
    return render(request, "encyclopedia/entry.html", {
        "title": title,
        "content": content
    })

def search(request):
    query = request.GET.get('q', '').lower()
    entries = util.list_entries()
    if query in [entry.lower() for entry in entries]:
        return redirect('entry', title=query)
    
    results = list(sorted([entry for entry in entries 
          if query in entry.lower()]))
    return render(request, "encyclopedia/search.html", {
        "results": results,
        "query": query
    })

def new(request):
    if request.method == "POST":
        title = request.POST["title"]
        content = request.POST["content"]
        
        if util.get_entry(title):
            messages.error(request, f"Entry '{title}' already exists")
            return render(request, "encyclopedia/new.html")
            
        util.save_entry(title, content)
        return redirect('entry', title=title)
        
    return render(request, "encyclopedia/new.html")

