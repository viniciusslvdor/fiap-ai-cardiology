import { useState } from 'react';
import Badge from '../../components/Badge/Badge.jsx';
import Card from '../../components/Card/Card.jsx';
import EmptyState from '../../components/EmptyState/EmptyState.jsx';
import Icon from '../../components/Icon.jsx';
import Loading from '../../components/Loading/Loading.jsx';
import { useFakeApi } from '../../hooks/useFakeApi.js';
import { getPatients } from '../../services/api.js';
import { formatDate } from '../../utils/dates.js';
import styles from './Patients.module.css';

const SEX = { F: 'Female', M: 'Male' };

export default function Patients() {
  const { data: patients, loading, error } = useFakeApi(getPatients);
  const [search, setSearch] = useState('');
  const [riskFilter, setRiskFilter] = useState('all');

  const term = search.trim().toLowerCase();
  const filtered = patients.filter(
    (p) => p.name.toLowerCase().includes(term) && (riskFilter === 'all' || p.risk === riskFilter),
  );

  const filters = (
    <>
      <label className={styles.search}>
        <Icon name="search" size={16} />
        <span className="sr-only">Search patient</span>
        <input
          className="input"
          type="search"
          placeholder="Search by name..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </label>
      <label>
        <span className="sr-only">Filter by risk</span>
        <select className="input" value={riskFilter} onChange={(e) => setRiskFilter(e.target.value)}>
          <option value="all">All risk levels</option>
          <option value="high">High</option>
          <option value="moderate">Moderate</option>
          <option value="low">Low</option>
        </select>
      </label>
    </>
  );

  return (
    <Card title={`Patients${loading ? '' : ` (${filtered.length})`}`} actions={filters} noPadding>
      {loading && <Loading text="Loading patients..." />}
      {error && <EmptyState title="Error loading patients" description={error} />}
      {!loading && !error && filtered.length === 0 && (
        <EmptyState title="No patients found" description="Adjust the search or the risk filter.">
          <button
            className="btn btn-ghost"
            onClick={() => {
              setSearch('');
              setRiskFilter('all');
            }}
          >
            Clear filters
          </button>
        </EmptyState>
      )}

      {!loading && !error && filtered.length > 0 && (
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Name</th>
                <th>Age</th>
                <th>Sex</th>
                <th>Last visit</th>
                <th>Status</th>
                <th>Risk</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.id}>
                  <td data-label="Name" className={styles.name}>
                    {p.name}
                  </td>
                  <td data-label="Age">{p.age} years</td>
                  <td data-label="Sex">{SEX[p.sex] ?? p.sex}</td>
                  <td data-label="Last visit">{formatDate(p.lastVisit)}</td>
                  <td data-label="Status">
                    <Badge value={p.status} />
                  </td>
                  <td data-label="Risk">
                    <Badge value={p.risk} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
