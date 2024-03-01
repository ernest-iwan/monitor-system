from django.shortcuts import render

def status(request, slug):
    context = {
        "slug": slug,
    }
    return render(request, 'status_page/status.html', context)
