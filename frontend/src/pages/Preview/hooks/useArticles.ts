// frontend/src/pages/Preview/hooks/useArticles.ts
import { useState, useEffect, useCallback } from 'react';
import { getArticles } from '../../../api';
import { useFilter } from '../context/FilterContext';

interface Article {
  id: number;
  title: string;
  summary: string;
  cover_image: string;
  url: string;
  author: string;
  publish_time: string;
  created_at: string;
  rule_name: string;
  tags: string[];
}

interface UseArticlesResult {
  articles: Article[];
  loading: boolean;
  loadingMore: boolean;
  hasMore: boolean;
  loadMore: () => void;
  refresh: () => void;
  total: number;
}

export function useArticles(): UseArticlesResult {
  const { filter } = useFilter();
  const [articles, setArticles] = useState<Article[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [skip, setSkip] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [total, setTotal] = useState(0);
  const LIMIT = 20;

  const buildParams = useCallback((offset: number) => {
    const params: any = {
      skip: offset,
      limit: LIMIT,
      status: 'success',
    };
    if (filter.keyword) params.keyword = filter.keyword;
    if (filter.source) params.source = filter.source;
    if (filter.timeRange) params.time_range = filter.timeRange;
    if (filter.tags.length > 0) params.tags = filter.tags.join(',');
    return params;
  }, [filter]);

  const loadArticles = useCallback(async (offset: number, isLoadMore = false) => {
    if (isLoadMore) {
      setLoadingMore(true);
    } else {
      setLoading(true);
    }

    try {
      const res = await getArticles(buildParams(offset));
      const newArticles = res.data;
      const totalCount = parseInt(res.headers['x-total-count'] || '0');

      if (isLoadMore) {
        setArticles(prev => [...prev, ...newArticles]);
      } else {
        setArticles(newArticles);
      }

      setTotal(totalCount);
      setHasMore(offset + newArticles.length < totalCount);
      setSkip(offset + newArticles.length);
    } catch (error) {
      console.error('Failed to load articles:', error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [buildParams]);

  useEffect(() => {
    setSkip(0);
    setHasMore(true);
    loadArticles(0);
  }, [filter, loadArticles]);

  const loadMore = useCallback(() => {
    if (!loadingMore && hasMore) {
      loadArticles(skip, true);
    }
  }, [loadArticles, skip, loadingMore, hasMore]);

  const refresh = useCallback(() => {
    setSkip(0);
    setHasMore(true);
    loadArticles(0);
  }, [loadArticles]);

  return { articles, loading, loadingMore, hasMore, loadMore, refresh, total };
}