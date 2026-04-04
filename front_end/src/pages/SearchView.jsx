import React, { useState } from 'react';
import { Search, SlidersHorizontal, Star } from 'lucide-react';
import api from '../services/api';

export default function SearchView() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState('keyword'); // keyword, text-score, phrase
  const [meta, setMeta] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query) return;

    try {
      setLoading(true);
      let endpoint = `/phones/search/${mode}?q=${query}`;
      if (mode === 'text-score') {
         endpoint = `/phones/search/score?q=${query}`;
      } else if (mode === 'phrase') {
         endpoint = `/phones/search/phrase?phrase=${query}`;
      }

      const res = await api.get(endpoint);
      setResults(res.results || []);
      setMeta({ count: res.count, stats: res.stats });
    } catch (err) {
      alert(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight text-slate-900">Advanced Search</h2>

      <div className="glass rounded-xl p-6">
        <form onSubmit={handleSearch} className="flex gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 w-5 h-5 text-slate-400" />
            <input 
              value={query} onChange={(e) => setQuery(e.target.value)}
              placeholder="Search smartphones ($text index)..."
              className="w-full pl-10 pr-4 py-2 border rounded-lg focus:ring-2 outline-none focus:ring-primary-500"
            />
          </div>
          <select 
            value={mode} onChange={(e) => setMode(e.target.value)}
            className="px-4 py-2 border rounded-lg bg-white"
          >
            <option value="keyword">Any Keyword</option>
            <option value="phrase">Exact Phrase</option>
            <option value="text-score">Relevance Ranked</option>
          </select>
          <button 
            type="submit" disabled={loading}
            className="px-6 py-2 bg-primary-600 text-white font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
      </div>

      {meta && (
        <div className="text-sm text-slate-500">
          Found {meta.count} results. {meta.stats && `(Scanned ${meta.stats.docs_examined} docs in ${meta.stats.execution_time_ms}ms)`}
        </div>
      )}

      {results.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {results.map(phone => (
            <div key={phone._id} className="glass rounded-xl p-5 hover:border-primary-200 transition-colors flex flex-col group">
              <div className="flex justify-between items-start mb-2">
                <div className="flex flex-col gap-1">
                  <h3 className="font-bold text-lg text-slate-900 leading-tight flex items-center gap-2">
                    {phone.name}
                    <button 
                      onClick={() => {
                        navigator.clipboard.writeText(phone._id);
                        alert('ID Copied: ' + phone._id);
                      }}
                      className="p-1 hover:bg-slate-100 rounded text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity"
                      title="Copy ID"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-copy"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                    </button>
                  </h3>
                  <p className="text-[10px] font-mono text-slate-400">ID: ..{phone._id?.slice(-6)}</p>
                </div>
                {phone.score && (
                  <span className="flex items-center gap-1 text-xs font-semibold text-amber-600 bg-amber-50 px-2 py-1 rounded">
                    <Star className="w-3 h-3"/> {phone.score.toFixed(2)}
                  </span>
                )}
              </div>
              <p className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600 mb-3">
                {phone.brand}
              </p>
              <p className="text-sm text-slate-600 line-clamp-3 mb-4">
                {phone.description}
              </p>
              <div className="mt-auto flex items-center justify-between">
                <span className="text-lg font-bold text-emerald-600">${phone.price}</span>
              </div>
            </div>
          ))}
        </div>
      )}
      
      {!loading && meta && results.length === 0 && (
        <div className="text-center py-12 text-slate-400">
          No smartphones matched your search.
        </div>
      )}
    </div>
  );
}
