import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { BarChart3, Brain, Download, LogOut, Plus, Search, ShieldCheck, Trash2, Upload } from 'lucide-react';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
  ArcElement,
} from 'chart.js';
import { api, clearToken, getToken, setToken } from './services/api';
import './styles.css';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, LineElement, PointElement, Tooltip, Legend);

const blankEmployee = {
  Age: 31,
  BusinessTravel: 'Travel_Rarely',
  Department: 'Research & Development',
  DistanceFromHome: 8,
  EducationField: 'Life Sciences',
  Gender: 'Male',
  JobRole: 'Research Scientist',
  JobLevel: 2,
  MonthlyIncome: 6200,
  NumCompaniesWorked: 2,
  OverTime: 'No',
  PercentSalaryHike: 14,
  StockOptionLevel: 1,
  TotalWorkingYears: 8,
  TrainingTimesLastYear: 3,
  EnvironmentSatisfaction: 3,
  JobSatisfaction: 3,
  RelationshipSatisfaction: 3,
  WorkLifeBalance: 3,
  YearsAtCompany: 5,
  YearsInCurrentRole: 3,
  YearsSinceLastPromotion: 1,
  YearsWithCurrManager: 3,
  Attrition: 'No',
};

function App() {
  const [tokenReady, setTokenReady] = useState(Boolean(getToken()));
  return tokenReady ? <Workspace onLogout={() => { clearToken(); setTokenReady(false); }} /> : <Login onLogin={() => setTokenReady(true)} />;
}

function Login({ onLogin }) {
  const [email, setEmail] = useState('admin@hr.local');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');

  async function submit(event) {
    event.preventDefault();
    setError('');
    try {
      const result = await api.login(email, password);
      setToken(result.access_token);
      onLogin();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="login-screen">
      <section className="login-panel">
        <div className="brand-mark"><ShieldCheck size={30} /></div>
        <h1>AI Employee Attrition Analytics</h1>
        <form onSubmit={submit}>
          <label>Email<input value={email} onChange={(event) => setEmail(event.target.value)} /></label>
          <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
          {error && <p className="error">{error}</p>}
          <button type="submit">Login</button>
        </form>
      </section>
    </main>
  );
}

function Workspace({ onLogout }) {
  const [tab, setTab] = useState('dashboard');
  const [metrics, setMetrics] = useState(null);
  const [employees, setEmployees] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [editing, setEditing] = useState(null);
  const [notice, setNotice] = useState('');

  async function refresh() {
    const [m, e, a] = await Promise.all([api.dashboard(), api.employees(search), api.analytics()]);
    setMetrics(m);
    setEmployees(e);
    setAnalytics(a);
  }

  useEffect(() => { refresh().catch((err) => setNotice(err.message)); }, []);
  useEffect(() => { api.employees(search).then(setEmployees).catch((err) => setNotice(err.message)); }, [search]);

  async function runPrediction(employee) {
    setSelected(employee);
    const result = await api.predict(employee.id);
    setPrediction(result);
  }

  async function saveEmployee(employee) {
    if (employee.id) {
      await api.updateEmployee(employee.id, employee);
      setNotice('Employee updated');
    } else {
      await api.addEmployee(employee);
      setNotice('Employee added');
    }
    setEditing(null);
    await refresh();
  }

  async function deleteEmployee(id) {
    await api.deleteEmployee(id);
    setNotice('Employee deleted');
    await refresh();
  }

  async function uploadCsv(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    const data = new FormData();
    data.append('file', file);
    const result = await api.uploadEmployees(data);
    setNotice(`Imported ${result.imported} employees`);
    await refresh();
  }

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="app-title"><Brain size={26} /><span>Attrition AI</span></div>
        <NavButton active={tab === 'dashboard'} onClick={() => setTab('dashboard')} icon={<BarChart3 size={18} />} label="Dashboard" />
        <NavButton active={tab === 'employees'} onClick={() => setTab('employees')} icon={<Search size={18} />} label="Employees" />
        <NavButton active={tab === 'reports'} onClick={() => setTab('reports')} icon={<Download size={18} />} label="Reports" />
        <button className="logout" onClick={onLogout}><LogOut size={18} />Logout</button>
      </aside>
      <section className="content">
        <header className="topbar">
          <div>
            <h1>{tab === 'dashboard' ? 'HR Analytics Dashboard' : tab === 'employees' ? 'Employee Management' : 'Reports'}</h1>
            <p>{metrics ? `${metrics.total_employees} employee records monitored` : 'Loading workspace'}</p>
          </div>
          {notice && <span className="notice">{notice}</span>}
        </header>
        {tab === 'dashboard' && <Dashboard metrics={metrics} analytics={analytics} />}
        {tab === 'employees' && (
          <Employees
            employees={employees}
            search={search}
            setSearch={setSearch}
            onPredict={runPrediction}
            selected={selected}
            prediction={prediction}
            onAdd={() => setEditing(blankEmployee)}
            onEdit={setEditing}
            onDelete={deleteEmployee}
            onUpload={uploadCsv}
          />
        )}
        {tab === 'reports' && <Reports />}
      </section>
      {editing && <EmployeeModal initial={editing} onClose={() => setEditing(null)} onSave={saveEmployee} />}
    </main>
  );
}

function NavButton({ active, onClick, icon, label }) {
  return <button className={active ? 'nav active' : 'nav'} onClick={onClick}>{icon}<span>{label}</span></button>;
}

function Dashboard({ metrics, analytics }) {
  if (!metrics || !analytics) return <div className="loading">Loading analytics...</div>;
  const departments = Object.entries(metrics.departments);
  return (
    <>
      <section className="metric-grid">
        <Metric label="Total Employees" value={metrics.total_employees} />
        <Metric label="Employees At Risk" value={metrics.employees_at_risk} tone="risk" />
        <Metric label="Average Salary" value={`$${Math.round(metrics.average_salary).toLocaleString()}`} />
        <Metric label="Attrition Rate" value={`${Math.round(metrics.attrition_rate * 100)}%`} tone="risk" />
      </section>
      <section className="chart-grid">
        <ChartPanel title="Attrition by Department">
          <Bar data={barData(analytics.attrition_by_department, 'attrition', '#d45c4c')} options={chartOptions} />
        </ChartPanel>
        <ChartPanel title="Department Mix">
          <Doughnut data={{ labels: departments.map(([label]) => label), datasets: [{ data: departments.map(([, value]) => value), backgroundColor: ['#2f6f73', '#d4a24c', '#7c6aa8'] }] }} />
        </ChartPanel>
        <ChartPanel title="Overtime vs Attrition">
          <Bar data={barData(analytics.overtime_vs_attrition, 'rate', '#8a5b3f')} options={chartOptions} />
        </ChartPanel>
        <ChartPanel title="Income Distribution">
          <Line data={lineData(analytics.income_distribution)} options={chartOptions} />
        </ChartPanel>
      </section>
    </>
  );
}

function Metric({ label, value, tone }) {
  return <article className={`metric ${tone || ''}`}><span>{label}</span><strong>{value}</strong></article>;
}

function ChartPanel({ title, children }) {
  return <article className="chart-panel"><h2>{title}</h2><div className="chart-box">{children}</div></article>;
}

function Employees({ employees, search, setSearch, onPredict, selected, prediction, onAdd, onEdit, onDelete, onUpload }) {
  return (
    <section className="employee-layout">
      <div className="employee-main">
        <div className="toolbar">
          <label className="search"><Search size={17} /><input placeholder="Search department, role, gender" value={search} onChange={(event) => setSearch(event.target.value)} /></label>
          <label className="icon-button"><Upload size={18} /><input type="file" accept=".csv" onChange={onUpload} /></label>
          <button className="icon-button" onClick={onAdd}><Plus size={18} /></button>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>ID</th><th>Department</th><th>Role</th><th>Overtime</th><th>Satisfaction</th><th>Income</th><th></th></tr></thead>
            <tbody>
              {employees.map((employee) => (
                <tr key={employee.id}>
                  <td>#{employee.id}</td>
                  <td>{employee.Department}</td>
                  <td>{employee.JobRole}</td>
                  <td>{employee.OverTime}</td>
                  <td>{employee.JobSatisfaction}/4</td>
                  <td>${Number(employee.MonthlyIncome).toLocaleString()}</td>
                  <td className="actions">
                    <button onClick={() => onPredict(employee)}>Predict</button>
                    <button onClick={() => onEdit(employee)}>Edit</button>
                    <button className="danger" onClick={() => onDelete(employee.id)}><Trash2 size={16} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <PredictionPanel selected={selected} prediction={prediction} />
    </section>
  );
}

function PredictionPanel({ selected, prediction }) {
  return (
    <aside className="prediction-panel">
      <h2>Prediction</h2>
      {!prediction ? <p>Select an employee and run prediction.</p> : (
        <>
          <div className="risk-score"><span>Employee #{selected?.id}</span><strong>{Math.round(prediction.probability * 100)}%</strong><em>{prediction.prediction}</em></div>
          <h3>Reasons</h3>
          <ul>{prediction.reasons.map((reason) => <li key={reason}>{reason}</li>)}</ul>
          <h3>Retention Actions</h3>
          <ul>{prediction.recommendations.map((item) => <li key={item}>{item}</li>)}</ul>
        </>
      )}
    </aside>
  );
}

function EmployeeModal({ initial, onClose, onSave }) {
  const [form, setForm] = useState(initial);
  const numericFields = useMemo(() => new Set(['Age', 'DistanceFromHome', 'JobLevel', 'MonthlyIncome', 'NumCompaniesWorked', 'PercentSalaryHike', 'StockOptionLevel', 'TotalWorkingYears', 'TrainingTimesLastYear', 'EnvironmentSatisfaction', 'JobSatisfaction', 'RelationshipSatisfaction', 'WorkLifeBalance', 'YearsAtCompany', 'YearsInCurrentRole', 'YearsSinceLastPromotion', 'YearsWithCurrManager']), []);
  function update(key, value) {
    setForm((current) => ({ ...current, [key]: numericFields.has(key) ? Number(value) : value }));
  }
  return (
    <div className="modal-backdrop">
      <form className="modal" onSubmit={(event) => { event.preventDefault(); onSave(form); }}>
        <h2>{form.id ? 'Edit Employee' : 'Add Employee'}</h2>
        <div className="form-grid">
          {Object.keys(blankEmployee).map((key) => (
            <label key={key}>{key}<input value={form[key] ?? ''} type={numericFields.has(key) ? 'number' : 'text'} onChange={(event) => update(key, event.target.value)} /></label>
          ))}
        </div>
        <div className="modal-actions"><button type="button" onClick={onClose}>Cancel</button><button type="submit">Save</button></div>
      </form>
    </div>
  );
}

function Reports() {
  async function download(kind) {
    const token = getToken();
    const response = await fetch(api.reportUrl(kind), { headers: { Authorization: `Bearer ${token}` } });
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `employee_attrition_report.${kind === 'excel' ? 'xls' : kind}`;
    link.click();
    URL.revokeObjectURL(url);
  }
  return (
    <section className="report-grid">
      {['pdf', 'excel', 'csv'].map((kind) => (
        <button key={kind} className="report-tile" onClick={() => download(kind)}><Download size={28} /><span>{kind.toUpperCase()} Report</span></button>
      ))}
    </section>
  );
}

const chartOptions = { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } };
function barData(rows, field, color) {
  return { labels: rows.map((r) => r.label), datasets: [{ data: rows.map((r) => r[field]), backgroundColor: color, borderRadius: 4 }] };
}
function lineData(rows) {
  return { labels: rows.map((r) => r.label), datasets: [{ data: rows.map((r) => r.count), borderColor: '#2f6f73', backgroundColor: '#2f6f73', tension: 0.35 }] };
}

createRoot(document.getElementById('root')).render(<App />);
