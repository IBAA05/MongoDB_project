import React, { useState } from 'react';
import { Trash2, Edit, RefreshCw, PlusSquare, MinusSquare } from 'lucide-react';
import api from '../services/api';

export default function CRUDView() {
  const [loading, setLoading] = useState(false);
  const [deleteId, setDeleteId] = useState('');
  
  const [bulkDelete, setBulkDelete] = useState({ name: '', brand: '' });
  const [priceUpdate, setPriceUpdate] = useState({ brand: '', percentage: '' });
  const [removeField, setRemoveField] = useState('');
  
  const [updateId, setUpdateId] = useState('');
  const [updatePhone, setUpdatePhone] = useState({
    name: '', brand: '', description: '', price: '', category: '', stock: '', rating: ''
  });

  const execute = async (operation, payload) => {
    try {
      setLoading(true);
      const res = await operation(payload);
      alert('Success: ' + JSON.stringify(res));
    } catch (err) {
      alert('Error: ' + err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold tracking-tight text-slate-900">CRUD Operations</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Single Document Delete */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-rose-600">
            <Trash2 className="w-5 h-5" /> Delete Document
          </h3>
          <div className="flex gap-3">
            <input 
              value={deleteId} onChange={e => setDeleteId(e.target.value)}
              placeholder="Paste MongoDB _id here"
              className="flex-1 px-3 py-2 border rounded-lg text-sm"
            />
            <button 
              onClick={() => execute(() => api.delete(`/phones/${deleteId}`))}
              className="px-4 py-2 bg-rose-600 text-white rounded-lg hover:bg-rose-700 text-sm font-medium disabled:opacity-50"
              disabled={loading || !deleteId}
            >
              Delete
            </button>
          </div>
        </div>

        {/* Bulk Delete */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-rose-600">
            <Trash2 className="w-5 h-5" /> Bulk Delete
          </h3>
          <div className="flex gap-3">
            <input 
              value={bulkDelete.brand} onChange={e => setBulkDelete({...bulkDelete, brand: e.target.value})}
              placeholder="Brand to delete"
              className="w-1/2 px-3 py-2 border rounded-lg text-sm"
            />
            <input 
              value={bulkDelete.name} onChange={e => setBulkDelete({...bulkDelete, name: e.target.value})}
              placeholder="Or exact Name"
              className="w-1/2 px-3 py-2 border rounded-lg text-sm"
            />
          </div>
          <button 
            onClick={() => execute(() => api.delete(`/phones/bulk/delete`, { params: bulkDelete }))}
            className="mt-3 w-full px-4 py-2 bg-slate-900 text-white rounded-lg hover:bg-slate-800 text-sm font-medium disabled:opacity-50"
            disabled={loading || (!bulkDelete.brand && !bulkDelete.name)}
          >
            Execute Bulk Delete
          </button>
        </div>

        {/* Bulk Price Update */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-blue-600">
            <RefreshCw className="w-5 h-5" /> Bulk Price Update ($mul)
          </h3>
          <div className="flex gap-3 text-sm">
             <input 
              value={priceUpdate.brand} onChange={e => setPriceUpdate({...priceUpdate, brand: e.target.value})}
              placeholder="Target Brand"
              className="flex-1 px-3 py-2 border rounded-lg"
            />
            <div className="relative">
              <input 
                type="number" value={priceUpdate.percentage} onChange={e => setPriceUpdate({...priceUpdate, percentage: e.target.value})}
                placeholder="Increase"
                className="w-24 px-3 py-2 border rounded-lg pr-8"
              />
              <span className="absolute right-3 top-2.5 text-slate-400">%</span>
            </div>
          </div>
          <button 
            onClick={() => execute(() => api.patch(`/phones/brand/${priceUpdate.brand}/price?percentage=${priceUpdate.percentage}`))}
            className="mt-3 w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm font-medium disabled:opacity-50"
            disabled={loading || !priceUpdate.brand || !priceUpdate.percentage}
          >
            Increase Prices
          </button>
        </div>

        {/* Schema Migration */}
        <div className="glass rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-purple-600">
            <Edit className="w-5 h-5" /> Schema Migrations
          </h3>
          <div className="space-y-4">
            <button 
              onClick={() => execute(() => api.patch('/phones/bulk/add-fields'))}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-emerald-100 text-emerald-700 rounded-lg hover:bg-emerald-200 text-sm font-medium"
            >
              <PlusSquare className="w-4 h-4"/> Add Default Fields to All ($set)
            </button>
            <div className="flex gap-3">
              <input 
                value={removeField} onChange={e => setRemoveField(e.target.value)}
                placeholder="Field name to drop"
                className="flex-1 px-3 py-2 border border-rose-200 rounded-lg text-sm"
              />
              <button 
                onClick={() => execute(() => api.patch(`/phones/bulk/remove-field?field_name=${removeField}`))}
                className="px-4 py-2 bg-rose-100 flex items-center gap-2 text-rose-700 rounded-lg hover:bg-rose-200 text-sm font-medium"
                disabled={loading || !removeField}
              >
                <MinusSquare className="w-4 h-4"/> Drop
              </button>
            </div>
          </div>
        </div>

        {/* Replace Document */}
        <div className="glass rounded-xl p-6 md:col-span-2">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2 text-indigo-600">
            <RefreshCw className="w-5 h-5" /> Replace Document ($replaceOne)
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="space-y-4">
              <div>
                <label className="block mb-1 font-medium text-slate-700 text-sm">Target ID</label>
                <input 
                  value={updateId} onChange={e => setUpdateId(e.target.value)}
                  placeholder="Paste MongoDB _id here"
                  className="w-full px-3 py-2 border rounded-lg text-sm"
                />
              </div>
              <p className="text-xs text-slate-500 italic bg-slate-50 p-2 rounded">
                Tip: Copy an ID from the Database tab to update a specific record.
              </p>
            </div>
            
            <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
              <input value={updatePhone.name} onChange={e => setUpdatePhone({...updatePhone, name: e.target.value})} placeholder="New Name" className="px-3 py-2 border rounded-lg text-sm" />
              <input value={updatePhone.brand} onChange={e => setUpdatePhone({...updatePhone, brand: e.target.value})} placeholder="New Brand" className="px-3 py-2 border rounded-lg text-sm" />
              <input type="number" step="0.01" value={updatePhone.price} onChange={e => setUpdatePhone({...updatePhone, price: e.target.value})} placeholder="New Price" className="px-3 py-2 border rounded-lg text-sm" />
              <select value={updatePhone.category} onChange={e => setUpdatePhone({...updatePhone, category: e.target.value})} className="px-3 py-2 border rounded-lg text-sm">
                <option value="">Category...</option>
                <option value="budget">Budget</option>
                <option value="mid-range">Mid-Range</option>
                <option value="flagship">Flagship</option>
              </select>
              <textarea value={updatePhone.description} onChange={e => setUpdatePhone({...updatePhone, description: e.target.value})} placeholder="New Description" className="md:col-span-2 px-3 py-2 border rounded-lg text-sm" rows="2" />
              
              <button 
                onClick={() => {
                  // Construct payload with only non-empty fields
                  const payload = {};
                  if (updatePhone.name) payload.name = updatePhone.name;
                  if (updatePhone.brand) payload.brand = updatePhone.brand;
                  if (updatePhone.description) payload.description = updatePhone.description;
                  if (updatePhone.category) payload.category = updatePhone.category;
                  if (updatePhone.price) payload.price = parseFloat(updatePhone.price);
                  if (updatePhone.stock) payload.stock = parseInt(updatePhone.stock);
                  if (updatePhone.rating) payload.rating = parseFloat(updatePhone.rating);

                  execute(() => api.patch(`/phones/${updateId}`, payload));
                }}
                className="md:col-span-2 py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 text-sm disabled:opacity-50 transition-colors"
                disabled={loading || !updateId || Object.values(updatePhone).every(v => !v)}
              >
                Update Document (Partial)
              </button>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
