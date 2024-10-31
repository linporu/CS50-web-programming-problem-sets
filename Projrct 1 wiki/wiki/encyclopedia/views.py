from django.shortcuts import render
from django.http import HttpResponseRedirect
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
        return HttpResponseRedirect(reverse('entry', kwargs={'title': query}))
    
    results = list(sorted([entry for entry in entries 
          if query in entry.lower()]))
    return render(request, "encyclopedia/search.html", {
        "results": results,
        "query": query
    })

