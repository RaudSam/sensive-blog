from django.shortcuts import render
from blog.models import Comment, Post, Tag
from django.db.models import Count, Prefetch


def serialize_post_optimized(post):
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': tag.posts_count,
    }


def index(request):
    tags_with_posts_count = Tag.objects.annotate(posts_count=Count("posts"))

    most_popular_posts = (
        Post.objects
        .popular()
        .prefetch_related(Prefetch(
            'tags', queryset=tags_with_posts_count))
        .prefetch_related('author')
        .fetch_with_comments_count()[:5]
    )

    fresh_posts = (
        Post.objects
        .order_by('-published_at')
        .annotate(comments_count=Count('comments', distinct=True)) 
        .prefetch_related(Prefetch(
            'tags', queryset=tags_with_posts_count))
        .prefetch_related('author')
    )
    most_fresh_posts = fresh_posts[:5]

    most_popular_tags = Tag.objects.popular()[:5]

    context = {
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
        'page_posts': [
            serialize_post_optimized(post) for post in most_fresh_posts
        ],
        'popular_tags': [
            serialize_tag(tag) for tag in most_popular_tags
        ],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    tags_with_posts_count = Tag.objects.annotate(posts_count=Count("posts"))

    post = (
        Post.objects
        .prefetch_related('author')
        .prefetch_related(Prefetch(
            'tags', queryset=tags_with_posts_count))
        .get(slug=slug)
    )

    comments = (
        Comment.objects
        .filter(post=post)
        .prefetch_related('author')
    )
    serialized_comments = [{
        'text': comment.text,
        'published_at': comment.published_at,
        'author': comment.author.username,
    } for comment in comments]

    likes = post.likes.all()

    related_tags = post.tags.popular().annotate(posts_count=Count("posts"))

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': len(likes),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in post.tags.all()],
    }

    most_popular_tags = tags_with_posts_count.order_by('-posts_count')[:5]

    most_popular_posts = (
        Post.objects
        .popular()[:5]
        .fetch_with_comments_count()
        .prefetch_related(Prefetch(
            'tags', tags_with_posts_count))
        .prefetch_related('author')
    )

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
    }

    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tags_with_posts_count = Tag.objects.annotate(posts_count=Count("posts"))

    tag = Tag.objects.get(title=tag_title)

    most_popular_tags = tags_with_posts_count.order_by('-posts_count')[:5]

    most_popular_posts = (
        Post.objects
        .popular()[:5]
        .fetch_with_comments_count()
        .prefetch_related(
            Prefetch('tags',
                     queryset=tags_with_posts_count)
                     )
        .prefetch_related('author')
    )

    related_posts = (
        tag.posts
        .popular
        .prefetch_related('author')
        .fetch_with_comments_count()
        .prefetch_related(
            Prefetch('tags',
                     queryset=tags_with_posts_count)
                     )
        [:20]
    )

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post_optimized(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
