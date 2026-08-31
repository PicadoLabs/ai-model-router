import React, { useEffect, useState } from 'react';
import { Layers, Plus, Trash2, CheckCircle, Sliders, ToggleLeft, ToggleRight } from 'lucide-react';
import { fetchApi } from '../lib/api';
import { RoutingRule } from '../types';

export const Rules: React.FC = () => {
  const [rules, setRules] = useState<RoutingRule[]>([]);
  const [showAddModal, setShowAddModal] = useState(false);

  const [newRule, setNewRule] = useState<Partial<RoutingRule>>({
    name: '',
    description: '',
    priority: 10,
    is_enabled: true,
    condition_field: 'task_type',
    condition_operator: '==',
    condition_value: 'DEBUGGING',
    action_type: 'FORCE_TIER',
    action_target: 'POWER',
  });

  const loadRules = async () => {
    try {
      const data = await fetchApi<RoutingRule[]>('/api/rules');
      setRules(data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  const handleToggle = async (rule: RoutingRule) => {
    try {
      await fetchApi(`/api/rules/${rule.id}`, {
        method: 'PUT',
        body: JSON.stringify({ ...rule, is_enabled: !rule.is_enabled }),
      });
      loadRules();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this routing rule?')) return;
    try {
      await fetchApi(`/api/rules/${id}`, { method: 'DELETE' });
      loadRules();
    } catch (err) {
      console.error(err);
    }
  };

  const handleAddRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRule.name) return;
    try {
      await fetchApi('/api/rules', {
        method: 'POST',
        body: JSON.stringify(newRule),
      });
      setShowAddModal(false);
      loadRules();
    } catch (err: any) {
      alert(`Error: ${err.message}`);
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-16">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-border-subtle pb-4">
        <div>
          <h2 className="text-xl font-bold font-mono text-text-primary tracking-wide flex items-center gap-2">
            <Layers className="w-5 h-5 text-accent-primary" />
            VISUAL ROUTING RULES BUILDER
          </h2>
          <p className="text-xs text-text-muted font-mono mt-1">
            Build deterministic policy overrides, budget guards, and task routing constraints without writing code.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-accent-primary text-bg-primary font-mono text-xs font-bold hover:brightness-110 shadow-[0_0_12px_rgba(77,163,255,0.3)] transition-all"
        >
          <Plus className="w-3.5 h-3.5" /> ADD ROUTING RULE
        </button>
      </div>

      {/* Rules Visual Blocks List */}
      <div className="space-y-4 font-mono text-xs">
        {rules.length === 0 ? (
          <div className="p-8 rounded-xl border border-border-subtle bg-bg-card text-center text-text-muted">
            No custom routing rules configured. System is running under default policy scoring.
          </div>
        ) : (
          rules.map((rule) => (
            <div
              key={rule.id}
              className={`p-5 rounded-xl border transition-all ${
                rule.is_enabled
                  ? 'border-border-subtle bg-bg-card'
                  : 'border-border-subtle/50 bg-bg-secondary/40 opacity-60'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-border-subtle pb-3">
                <div className="flex items-center gap-2.5">
                  <button onClick={() => handleToggle(rule)} className="text-text-muted hover:text-text-primary">
                    {rule.is_enabled ? (
                      <ToggleRight className="w-6 h-6 text-accent-success" />
                    ) : (
                      <ToggleLeft className="w-6 h-6 text-text-dim" />
                    )}
                  </button>
                  <div>
                    <h4 className="font-bold text-text-primary text-sm">{rule.name}</h4>
                    <p className="text-[11px] text-text-muted font-normal">{rule.description || 'Priority rule'}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-[11px] px-2 py-0.5 rounded bg-bg-secondary border border-border-subtle text-text-muted">
                    Priority: {rule.priority}
                  </span>
                  <button
                    onClick={() => handleDelete(rule.id)}
                    className="p-1.5 rounded hover:bg-accent-error/20 hover:text-accent-error text-text-dim transition-all"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Visual Rule Condition Block Diagram */}
              <div className="pt-4 flex flex-wrap items-center gap-2.5 text-xs">
                
                {/* IF condition block */}
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-bg-primary border border-border-subtle text-text-primary">
                  <span className="text-accent-primary font-bold text-[10px]">IF</span>
                  <span className="text-text-muted uppercase text-[11px]">{rule.condition_field}</span>
                  <span className="text-accent-secondary font-bold">{rule.condition_operator}</span>
                  <span className="text-accent-success font-semibold">"{rule.condition_value}"</span>
                </div>

                <span className="text-text-dim font-bold">→</span>

                {/* THEN action block */}
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-bg-primary border border-border-subtle text-text-primary">
                  <span className="text-accent-secondary font-bold text-[10px]">THEN</span>
                  <span className="text-text-muted uppercase text-[11px]">{rule.action_type}</span>
                  <span className="text-text-primary font-bold">{rule.action_target}</span>
                </div>

              </div>

            </div>
          ))
        )}
      </div>

      {/* Modal to add rule */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 font-mono">
          <div className="bg-bg-card border border-border-subtle rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
            <h3 className="text-sm font-bold text-text-primary uppercase tracking-wider">
              Create Routing Rule
            </h3>

            <form onSubmit={handleAddRule} className="space-y-3 text-xs">
              <div>
                <label className="text-text-muted block mb-1">Rule Name:</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Force Power Model on Math & Proofs"
                  value={newRule.name}
                  onChange={(e) => setNewRule({ ...newRule, name: e.target.value })}
                  className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2 text-text-primary outline-none"
                />
              </div>

              <div>
                <label className="text-text-muted block mb-1">Description:</label>
                <input
                  type="text"
                  placeholder="e.g. Ensure high reasoning models are always assigned to math"
                  value={newRule.description}
                  onChange={(e) => setNewRule({ ...newRule, description: e.target.value })}
                  className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2 text-text-primary outline-none"
                />
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="text-text-muted block mb-1">Condition Field:</label>
                  <select
                    value={newRule.condition_field}
                    onChange={(e) => setNewRule({ ...newRule, condition_field: e.target.value })}
                    className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2 text-text-primary outline-none"
                  >
                    <option value="task_type">task_type</option>
                    <option value="complexity">complexity</option>
                    <option value="budget_percent">budget_percent</option>
                    <option value="context_size">context_size</option>
                  </select>
                </div>
                <div>
                  <label className="text-text-muted block mb-1">Operator:</label>
                  <select
                    value={newRule.condition_operator}
                    onChange={(e) => setNewRule({ ...newRule, condition_operator: e.target.value })}
                    className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2 text-text-primary outline-none"
                  >
                    <option value="==">==</option>
                    <option value="!=">!=</option>
                    <option value=">=">&gt;=</option>
                    <option value="<=">&lt;=</option>
                    <option value=">">&gt;</option>
                    <option value="<">&lt;</option>
                  </select>
                </div>
                <div>
                  <label className="text-text-muted block mb-1">Value:</label>
                  <input
                    type="text"
                    required
                    value={newRule.condition_value}
                    onChange={(e) => setNewRule({ ...newRule, condition_value: e.target.value })}
                    className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2 text-text-primary outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-text-muted block mb-1">Action Type:</label>
                  <select
                    value={newRule.action_type}
                    onChange={(e) => setNewRule({ ...newRule, action_type: e.target.value })}
                    className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2 text-text-primary outline-none"
                  >
                    <option value="FORCE_TIER">FORCE_TIER</option>
                    <option value="ROUTE_TO">ROUTE_TO</option>
                    <option value="SET_POLICY">SET_POLICY</option>
                  </select>
                </div>
                <div>
                  <label className="text-text-muted block mb-1">Action Target:</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. POWER or lowest_cost"
                    value={newRule.action_target}
                    onChange={(e) => setNewRule({ ...newRule, action_target: e.target.value })}
                    className="w-full rounded-lg border border-border-subtle bg-bg-primary p-2 text-text-primary outline-none"
                  />
                </div>
              </div>

              <div className="pt-4 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-lg border border-border-subtle bg-bg-secondary text-text-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-accent-primary text-bg-primary font-bold hover:brightness-110"
                >
                  Save Rule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
};
