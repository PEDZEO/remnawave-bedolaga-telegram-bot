from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.cabinet.routes import admin_news, news


pytestmark = pytest.mark.asyncio


def build_article(article_id: int, *, title: str, slug: str, is_published: bool = True) -> SimpleNamespace:
    return SimpleNamespace(
        id=article_id,
        title=title,
        slug=slug,
        content='<p>body</p>',
        excerpt='excerpt',
        category='Updates',
        category_color='#00e5a0',
        tag='release',
        category_id=None,
        tag_id=None,
        featured_image_url=None,
        is_published=is_published,
        is_featured=False,
        published_at=None,
        read_time_minutes=3,
        views_count=0,
        created_at=None,
        updated_at=None,
        author=None,
    )


async def test_admin_list_all_news_uses_single_session_sequentially(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    async def fake_get_all_news(_db, *, limit: int, offset: int):
        calls.append(f'items:{limit}:{offset}')
        return [build_article(1, title='Admin article', slug='admin-article', is_published=False)]

    async def fake_get_all_news_count(_db):
        calls.append('count')
        return 1

    monkeypatch.setattr(admin_news, 'get_all_news', fake_get_all_news)
    monkeypatch.setattr(admin_news, 'get_all_news_count', fake_get_all_news_count)

    response = await admin_news.list_all_news(
        admin=SimpleNamespace(id=1),
        db=SimpleNamespace(),
        limit=20,
        offset=0,
    )

    assert calls == ['items:20:0', 'count']
    assert response.total == 1
    assert len(response.items) == 1
    assert response.items[0].slug == 'admin-article'


async def test_public_list_news_uses_single_session_sequentially(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    async def fake_get_published_news(_db, *, category: str | None, limit: int, offset: int):
        calls.append(f'items:{category}:{limit}:{offset}')
        return [build_article(2, title='Public article', slug='public-article', is_published=True)]

    async def fake_get_published_news_count(_db, *, category: str | None):
        calls.append(f'count:{category}')
        return 1

    async def fake_get_news_categories(_db):
        calls.append('categories')
        return ['Updates']

    monkeypatch.setattr(news, 'get_published_news', fake_get_published_news)
    monkeypatch.setattr(news, 'get_published_news_count', fake_get_published_news_count)
    monkeypatch.setattr(news, 'get_news_categories', fake_get_news_categories)

    response = await news.list_published_news(
        user=SimpleNamespace(id=1),
        db=SimpleNamespace(),
        category='Updates',
        limit=20,
        offset=0,
    )

    assert calls == ['items:Updates:20:0', 'count:Updates', 'categories']
    assert response.total == 1
    assert response.categories == ['Updates']
    assert len(response.items) == 1
    assert response.items[0].slug == 'public-article'
