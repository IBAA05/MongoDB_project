import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import { Activity, Smartphone, DollarSign, TrendingUp } from 'lucide-react';
import api from '../services/api';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

export default function Dashboard() {
  const [stats, setStats] = useState({
    total: 0,
    priceStats: { avg_price: 0, min_price: 0, max_price: 0 },
    topBrand: { _id: '', count: 0 },
  });
  
  const [brandsData, setBrandsData] = useState([]);
  const [priceDistData, setPriceDistData] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [
          countRes, 
          priceRes, 
          topBrandRes, 
          brandsAggRes,
          distRes
        ] = await Promise.all([
          api.get('/phones/stats/count'),
          api.get('/phones/stats/price'),
          api.get('/phones/stats/top-brand-count'),
          api.get('/phones/aggregations/group-by-brand'),
          api.get('/phones/stats/price-distribution')
        ]);

        setStats({
          total: countRes.total_phones || 0,
          priceStats: priceRes || { avg_price: 0, min_price: 0, max_price: 0 },
          topBrand: topBrandRes || { brand: '', count: 0 }
        });

        // The brand aggregation returns: { results: [{brand, total_phones, avg_price}] }
        setBrandsData(brandsAggRes.results || []);
        
        // Transform price distribution list: [{bracket, count}, ...] -> { labels: [], data: [] }
        const distList = distRes.distribution || [];
        setPriceDistData({
          labels: distList.map(item => item.bracket),
          data: distList.map(item => item.count)
        });

      } catch (err) {
        console.error("Dashboard error:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const brandChartData = {
    labels: brandsData.map(d => d.brand),
    datasets: [
      {
        label: 'Phones per Brand',
        data: brandsData.map(d => d.total_phones),
        backgroundColor: 'rgba(14, 165, 233, 0.5)',
        borderColor: 'rgb(14, 165, 233)',
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const distChartData = {
    labels: priceDistData.labels || [],
    datasets: [
      {
        label: 'Price Distribution',
        data: priceDistData.data || [],
        backgroundColor: 'rgba(16, 185, 129, 0.5)',
        borderColor: 'rgb(16, 185, 129)',
        borderWidth: 1,
        borderRadius: 4,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { position: 'top' },
    },
    scales: {
      y: { beginAtZero: true, ticks: { precision: 0 } }
    }
  };

  if (loading) return <div className="p-8 text-center text-slate-500">Loading dashboard...</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight text-slate-900">Dashboard</h2>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
        {/* Top-level stat cards */}
        <div className="glass rounded-xl p-6 flex items-start gap-4">
          <div className="p-3 bg-blue-100 text-blue-600 rounded-lg">
            <Smartphone className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Total Phones</p>
            <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
          </div>
        </div>

        <div className="glass rounded-xl p-6 flex items-start gap-4">
          <div className="p-3 bg-emerald-100 text-emerald-600 rounded-lg">
            <DollarSign className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Global Average Price</p>
            <p className="text-2xl font-bold text-slate-900">${stats.priceStats.avg_price?.toFixed(2)}</p>
          </div>
        </div>

        <div className="glass rounded-xl p-6 flex items-start gap-4">
          <div className="p-3 bg-purple-100 text-purple-600 rounded-lg">
            <TrendingUp className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Top Brand</p>
            <p className="text-2xl font-bold text-slate-900">{stats.topBrand.brand}</p>
            <p className="text-xs text-slate-400">{stats.topBrand.count} devices</p>
          </div>
        </div>

        <div className="glass rounded-xl p-6 flex items-start gap-4">
          <div className="p-3 bg-rose-100 text-rose-600 rounded-lg">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <p className="text-sm font-medium text-slate-500">Price Range</p>
            <p className="text-xl font-bold text-slate-900">
              ${stats.priceStats.min_price} - ${stats.priceStats.max_price}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass rounded-xl p-6 flex flex-col h-[400px]">
          <h3 className="text-lg font-semibold mb-4">Phones per Brand</h3>
          <div className="flex-1 relative">
            <Bar data={brandChartData} options={chartOptions} />
          </div>
        </div>

        <div className="glass rounded-xl p-6 flex flex-col h-[400px]">
          <h3 className="text-lg font-semibold mb-4">Price Distribution</h3>
          <div className="flex-1 relative">
            <Bar data={distChartData} options={chartOptions} />
          </div>
        </div>
      </div>
    </div>
  );
}
