from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.generic import ListView
from django.core.mail import send_mail
from django.db.models import Count
from taggit.models import Tag
from .models import Post,Comment
from .forms import EmailPostForm,CommentForm


# List All Posts with Normal Method.
def post_list(request,tag_slug=None):
    object_list = Post.published.all()
    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag,slug=tag_slug)
        object_list = object_list.filter(tags__in=[tag])
    paginator = Paginator(object_list, 2)
    page = request.GET.get('page')
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    return render(request, 'blog/post/list.html', {'posts': posts, 'page': page,'tag':tag})


# List all Posts using Class Based Views
class PostListView(ListView):
    queryset = Post.published.all()
    context_object_name = 'posts'
    paginate_by = 2
    template_name = 'blog/post/list.html'


# Load a Post Detail page.
# Render the Comment Model Form and save the Response to the DB.
def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post, slug=post, status='published', publish__year=year, publish__month=month,
                             publish__day=day)
    # Get the List of Active Comments for this post.
    comments = post.comments.filter(active=True)
    new_comment = None
    
    # Handle the Form Post Request.
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        # Check if the Form Fields are valid.
        if comment_form.is_valid():
            # Create a comment object and don't save it to the DB.
            new_comment = comment_form.save(commit=False)
            # Assign the current post object to this comment.
            new_comment.post = post
            new_comment.save()
    else:
        comment_form = CommentForm()
    post_tags_ids = post.tags.values_list('id', flat=True)
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags','-publish')[:4]
    print(similar_posts)
    return render(request, 'blog/post/detail.html', {'post': post,'comments':comments,'new_comment':new_comment,
    'comment_form':comment_form,'similar_posts':similar_posts})


# Render a Form to share the Post via Email.
def post_share(request, post_id):
    post = get_object_or_404(Post, id=post_id, status='published')
    sent = False
    if request.method == 'POST':
        # Form was Submitted
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Form fields passed Validation
            cd = form.cleaned_data
            # sent Email
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read " \
                      f"{post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, 'admin@myblog.com', [cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, 'blog/post/share.html', {'form': form, 'post': post, 'sent': sent})

