import React, { useEffect, useState } from 'react';
import { Database, Plus, Trash2 } from 'lucide-react';
import api from '../services/api';

export default function DatabaseView() {
  const [phones, setPhones] = useState([]);
  const [loading, setLoading] = useState(true);
  const [seeding, setSeeding] = useState(false);
  const [newPhone, setNewPhone] = useState({
    name: '', brand: '', description: '', price: '', category: '', stock: '', rating: ''
  });

  const fetchPhones = async () => {
    try {
      setLoading(true);
      const res = await api.get('/phones?limit=100');
      setPhones(res.phones || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPhones();
  }, []);

  const handleSeed = async () => {
    try {
      setSeeding(true);
      await api.post('/phones/seed');
      await fetchPhones();
      alert('Database seeded successfully!');
    } catch (err) {
      alert('Error seeding database: ' + err);
    } finally {
      setSeeding(false);
    }
  };

  const handleAddPhone = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...newPhone,
        price: parseFloat(newPhone.price),
        stock: newPhone.stock ? parseInt(newPhone.stock) : undefined,
        rating: newPhone.rating ? parseFloat(newPhone.rating) : undefined,
      };
      // Clean up undefineds
      Object.keys(payload).forEach(key => payload[key] === undefined && delete payload[key]);
      
      await api.post('/phones', payload);
      setNewPhone({ name: '', brand: '', description: '', price: '', category: '', stock: '', rating: '' });
      await fetchPhones();
      alert('Phone added!');
    } catch (err) {
      alert('Error: ' + err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-3xl font-bold tracking-tight text-slate-900">Database</h2>
        <button 
          onClick={handleSeed}
          disabled={seeding}
          className="flex items-center gap-2 px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 disabled:opacity-50"
        >
          <Database className="w-4 h-4" />
          {seeding ? 'Seeding...' : 'Seed Data'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 glass rounded-xl overflow-hidden flex flex-col h-[600px]">
          <div className="p-4 border-b border-slate-200 bg-white/50">
            <h3 className="font-semibold">All Phones ({phones.length})</h3>
          </div>
          <div className="overflow-y-auto p-0 flex-1">
            <table className="w-full text-left text-sm text-slate-600">
              <thead className="text-xs uppercase bg-slate-50 text-slate-700 sticky top-0">
                <tr>
                  <th className="px-4 py-3">ID</th>
                  <th className="px-4 py-3">Name</th>
                  <th className="px-4 py-3">Brand</th>
                  <th className="px-4 py-3 text-right">Price</th>
                </tr>
              </thead>
              <tbody className="divide-y text-xs divide-slate-100">
                {phones.map(phone => (
                  <tr key={phone._id} className="hover:bg-slate-50/50">
                    <td className="px-4 py-3 font-mono text-slate-400">
                      <div className="flex items-center gap-2 group">
                        <span>..{phone._id?.slice(-6)}</span>
                        <button 
                          onClick={() => {
                            navigator.clipboard.writeText(phone._id);
                            // Simple visual feedback could be added here if needed, 
                            // but standard browser alerts/success icons are often enough.
                            alert('ID Copied: ' + phone._id);
                          }}
                          className="p-1 hover:bg-slate-200 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Copy Full ID"
                        >
                          <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-copy"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                        </button>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-medium text-slate-900">{phone.name}</td>
                    <td className="px-4 py-3">{phone.brand}</td>
                    <td className="px-4 py-3 text-right">${phone.price}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="glass rounded-xl p-6 h-fit">
          <h3 className="font-semibold mb-4 flex items-center gap-2">
            <Plus className="w-4 h-4 text-emerald-500" />
            Add New Phone
          </h3>
          <form onSubmit={handleAddPhone} className="space-y-4 text-sm">
            <div>
              <label className="block mb-1 font-medium text-slate-700">Name</label>
              <input required value={newPhone.name} onChange={e => setNewPhone({...newPhone, name: e.target.value})} className="w-full px-3 py-2 border rounded-lg" placeholder="Model Name" />
            </div>
            <div>
              <label className="block mb-1 font-medium text-slate-700">Brand</label>
              <input required value={newPhone.brand} onChange={e => setNewPhone({...newPhone, brand: e.target.value})} className="w-full px-3 py-2 border rounded-lg" placeholder="Manufacturer" />
            </div>
            <div>
              <label className="block mb-1 font-medium text-slate-700">Price ($)</label>
              <input required type="number" step="0.01" value={newPhone.price} onChange={e => setNewPhone({...newPhone, price: e.target.value})} className="w-full px-3 py-2 border rounded-lg" placeholder="999.99" />
            </div>
            <div>
              <label className="block mb-1 font-medium text-slate-700">Description</label>
              <textarea required value={newPhone.description} onChange={e => setNewPhone({...newPhone, description: e.target.value})} className="w-full px-3 py-2 border rounded-lg" placeholder="Product details..." />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block mb-1 font-medium text-slate-700">Category</label>
                <select value={newPhone.category} onChange={e => setNewPhone({...newPhone, category: e.target.value})} className="w-full px-3 py-2 border rounded-lg">
                  <option value="">Select...</option>
                  <option value="budget">Budget</option>
                  <option value="mid-range">Mid-Range</option>
                  <option value="flagship">Flagship</option>
                </select>
              </div>
              <div>
                <label className="block mb-1 font-medium text-slate-700">Stock</label>
                <input type="number" value={newPhone.stock} onChange={e => setNewPhone({...newPhone, stock: e.target.value})} className="w-full px-3 py-2 border rounded-lg" placeholder="Units" />
              </div>
            </div>
            <button type="submit" className="w-full py-2 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700">
              Create Document
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
