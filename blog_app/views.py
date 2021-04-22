from django.shortcuts import render,get_object_or_404
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.views.generic import ListView
from django.core.mail import send_mail
from .models import Post
from .forms import EmailPostForm

# Create your views here.
def post_list(request):
    object_list = Post.published.all();
    paginator = Paginator(object_list,2);
    page = request.GET.get('page')
    try:
        posts = paginator.page(page);
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    return render(request,'blog/post/list.html',{'posts': posts,'page':page})

class PostListView(ListView):
    queryset = Post.published.all();
    context_object_name = 'posts';
    paginate_by = 2;
    template_name = 'blog/post/list.html';

def post_detail(request,year,month,day,post):
    post = get_object_or_404(Post,slug=post,status='published',publish__year=year,publish__month=month,publish__day=day);
    return render(request,'blog/post/detail.html',{'post':post})

def post_share(request,post_id):
    post = get_object_or_404(Post,id=post_id,status='published')
    sent = False
    if(request.method == 'POST'):
        # Form was Submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Form fields passed Validation
            cd = form.cleaned_data
            sent = True
            # sent Email
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read " \
            f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
            f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'admin@myblog.com', [cd['to']])
    else:
        form = EmailPostForm()
    return render(request,'blog/post/share.html',{'form':form,'post':post,'sent':sent})