---
layout: page
title: Hello from Jekyll-Bootstrap-Core
header: This is Jekyll-Bootstrap
---

## Blog

<div class="posts">
  {% for post in site.posts %}
		<div class="post">
			<div>
			<span>{{ post.date | date_to_string }}</span>
			<a href="{{ post.url }}">{{ post.title }}</a> &raquo;
			</div>
			<div class="content" style="display: hidden">
				{{ post.content | summarize }}
			</div>
    </div>
  {% endfor %}
</div>
