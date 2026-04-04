import React, { useEffect, useState } from 'react';
import { Layers, ChevronRight } from 'lucide-react';
import api from '../services/api';

export default function AnalyticsView() {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState({
    ranking: [],
    buckets: []
  });

  useEffect(() => {
    async function fetchAggregations() {
      try {
        const [rankingRes, bucketsRes] = await Promise.all([
          api.get('/phones/aggregations/brand-ranking'),
          api.get('/phones/aggregations/price-buckets')
        ]);
        
        setData({
          ranking: rankingRes.results || [],
          buckets: bucketsRes.tiers || []
        });
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchAggregations();
  }, []);

  if (loading) return <div className="p-8 text-center text-slate-500">Running aggregation pipelines...</div>;

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight text-slate-900">Advanced Aggregations</h2>
      <p className="text-slate-500">Exploring MongoDB `$group`, `$bucket`, and multi-stage pipelines.</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Brand Ranking by Price */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-500"/> Brand Ranking (Avg Price)
          </h3>
          <div className="space-y-3">
            {data.ranking.map((brand, i) => (
              <div key={brand._id} className="flex items-center justify-between p-3 bg-white rounded-lg border border-slate-100 shadow-sm">
                <div className="flex items-center gap-3">
                  <span className="text-slate-400 font-mono text-sm">#{i + 1}</span>
                  <span className="font-medium text-slate-700">{brand._id}</span>
                </div>
                <div className="text-right">
                  <div className="font-bold text-emerald-600">${brand.avg_price?.toFixed(2)}</div>
                  <div className="text-xs text-slate-400">{brand.total_phones} models</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Price Buckets */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-500"/> Market Segments ($bucket)
          </h3>
          <div className="space-y-4">
            {data.buckets.map((bucket) => {
              // Map bucket _id to human readable
              const tierName = bucket._id === 0 ? 'Budget (< $400)' : bucket._id === 400 ? 'Mid-Range ($400-$799)' : 'Flagship ($800+)';
              return (
                <div key={bucket._id} className="p-4 bg-slate-800 text-white rounded-xl">
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="font-semibold text-indigo-300">{tierName}</h4>
                    <span className="px-2 py-1 bg-slate-700 rounded text-xs font-medium">{bucket.count} items</span>
                  </div>
                  <div className="space-y-2">
                    {bucket.titles.slice(0, 3).map((title, i) => (
                      <div key={i} className="flex items-center text-sm text-slate-300">
                        <ChevronRight className="w-4 h-4 text-slate-500 mr-2"/>
                        {title}
                      </div>
                    ))}
                    {bucket.titles.length > 3 && (
                      <div className="text-xs text-slate-500 pl-6 italic">
                        + {bucket.titles.length - 3} more...
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

      </div>
    </div>
  );
}
