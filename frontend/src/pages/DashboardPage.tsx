import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Activity,
  AlertCircle,
  ArrowRight,
  ArrowUpRight,
  Bot,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Layers3,
  MailCheck,
  Sparkles,
  Target,
  TrendingUp,
  Users,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { apiClient } from '../api/client';
import { Badge } from '../components/Badge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { MetricCard } from '../components/MetricCard';

const SOURCE_COLORS = ['#7668e8', '#4d8df5', '#39b9c8', '#b17acb', '#ff8b83', '#6e9be8', '#51b89a'];
const STAGE_COLORS = ['#7668e8', '#5893f4', '#50b9c9', '#67a7ed', '#8980e9', '#53b998', '#f08c88'];
const tooltipStyle = {
  backgroundColor: '#ffffff',
  border: '1px solid #e5e8f3',
  borderRadius: '12px',
  boxShadow: '0 8px 24px rgba(37, 48, 102, 0.12)',
  color: '#263251',
  fontSize: '12px',
};

type BadgeVariant = NonNullable<React.ComponentProps<typeof Badge>['variant']>;

const getStatusVariant = (status: string): BadgeVariant => {
  if (status === 'completed') return 'success';
  if (status === 'awaiting_approval') return 'warning';
  if (status === 'failed') return 'danger';
  if (status === 'running' || status === 'pending') return 'info';
  return 'neutral';
};

const formatStatus = (status: string) => status.replaceAll('_', ' ');

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ['analyticsOverview'],
    queryFn: apiClient.getAnalyticsOverview,
    refetchInterval: 15000,
  });

  if (isLoading) {
    return <LoadingSpinner size="lg" label="Loading revenue analytics..." className="min-h-[400px]" />;
  }

  if (error || !metrics) {
    return (
      <div role="alert" className="rounded-2xl border border-rose-200 bg-white p-6 text-sm text-rose-700 shadow-sm">
        Failed to load revenue overview metrics. Please ensure backend service is operational.
      </div>
    );
  }

  const strongestSignal = metrics.leads_needing_attention.reduce<
    (typeof metrics.leads_needing_attention)[number] | null
  >((best, lead) => (
    !best || lead.conversion_probability > best.conversion_probability ? lead : best
  ), null);

  return (
    <div className="space-y-5 sm:space-y-6">
      <section className="relative overflow-hidden rounded-2xl border border-[#e6e8f6] bg-[linear-gradient(110deg,rgba(255,255,255,0.94)_0%,rgba(245,246,255,0.93)_58%,rgba(231,235,255,0.88)_100%)] px-5 py-5 shadow-[0_4px_20px_rgba(46,57,117,0.04)] sm:px-7 sm:py-6">
        <div className="pointer-events-none absolute -right-8 -top-24 h-56 w-56 rounded-full bg-[#b8c7ff]/25 blur-3xl" />
        <div className="relative flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
          <div>
            <div className="mb-2 flex items-center gap-2 text-[11px] font-semibold uppercase tracking-[0.15em] text-[#6c70c9]">
              <Sparkles className="h-3.5 w-3.5" />
              Sales intelligence
            </div>
            <h1 className="text-[25px] font-bold tracking-tight text-[#17203d] sm:text-[30px]">Pipeline at a glance</h1>
            <p className="mt-1.5 max-w-2xl text-sm leading-6 text-[#687391]">
              A live view of lead quality, conversion momentum, and the next opportunities to move forward.
            </p>
          </div>
          <div className="flex items-center gap-2 self-start rounded-xl border border-white/90 bg-white/70 px-3 py-2 text-xs font-medium text-[#64708f] shadow-sm sm:self-auto">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            Analytics refresh every 15 seconds
          </div>
        </div>
      </section>

      <section aria-label="Sales performance metrics" className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Total leads"
          value={metrics.total_leads}
          subtitle="Across all inbound and outbound sources"
          icon={Users}
          iconColor="text-blue-400"
          onClick={() => navigate('/leads')}
        />
        <MetricCard
          title="High-priority leads"
          value={metrics.high_priority_count}
          subtitle="Ranked by the current lead scoring"
          icon={Target}
          iconColor="text-rose-400"
          onClick={() => navigate('/leads?priority=high')}
        />
        <MetricCard
          title="Conversion rate"
          value={`${metrics.conversion_rate}%`}
          subtitle="Closed-won conversion across your leads"
          icon={TrendingUp}
          iconColor="text-emerald-400"
        />
        <MetricCard
          title="Overdue follow-ups"
          value={metrics.overdue_followups_count}
          subtitle={`${metrics.pending_approvals_count} drafts awaiting review`}
          icon={MailCheck}
          iconColor="text-violet-400"
          onClick={() => navigate('/follow-ups')}
        />
      </section>

      <section aria-label="Sales analytics charts" className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        <article className="surface-card min-w-0 p-4 sm:p-5 xl:col-span-5">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="rounded-xl bg-[#f0edff] p-2.5 text-[#7966df]">
                <Layers3 className="h-4 w-4" />
              </div>
              <div>
                <h2 className="section-heading">Lead pipeline</h2>
                <p className="section-description">Lead distribution across sales stages</p>
              </div>
            </div>
            <button type="button" onClick={() => navigate('/leads')} className="mt-1 inline-flex items-center gap-1 text-xs font-semibold text-[#6470d8] transition-colors hover:text-[#454fb8]">
              View leads <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
          <div className="h-[218px] min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics.leads_by_stage} margin={{ top: 8, right: 4, left: -22, bottom: 0 }} barCategoryGap="25%">
                <CartesianGrid vertical={false} stroke="#edf0f7" strokeDasharray="3 5" />
                <XAxis
                  dataKey="stage"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fill: '#7e88a4', fontSize: 10 }}
                  interval={0}
                  tickMargin={10}
                />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#929bb2', fontSize: 10 }} />
                <Tooltip contentStyle={tooltipStyle} cursor={{ fill: '#f6f7fc' }} />
                <Bar dataKey="count" name="Leads" radius={[7, 7, 2, 2]} maxBarSize={44}>
                  {metrics.leads_by_stage.map((stage, index) => (
                    <Cell key={stage.stage} fill={STAGE_COLORS[index % STAGE_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="surface-card min-w-0 p-4 sm:p-5 xl:col-span-4">
          <div className="mb-4 flex items-start gap-3">
            <div className="rounded-xl bg-[#e8f5ff] p-2.5 text-[#438be0]">
              <Activity className="h-4 w-4" />
            </div>
            <div>
              <h2 className="section-heading">Conversion trend</h2>
              <p className="section-description">Monthly lead conversion rate</p>
            </div>
          </div>
          <div className="h-[218px] min-w-0">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metrics.conversion_trend} margin={{ top: 10, right: 4, left: -18, bottom: 0 }}>
                <defs>
                  <linearGradient id="conversionFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#8069ed" stopOpacity={0.2} />
                    <stop offset="100%" stopColor="#8069ed" stopOpacity={0.015} />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="#edf0f7" strokeDasharray="3 5" />
                <XAxis dataKey="month" axisLine={false} tickLine={false} tick={{ fill: '#7e88a4', fontSize: 10 }} tickMargin={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fill: '#929bb2', fontSize: 10 }} unit="%" />
                <Tooltip
                  contentStyle={tooltipStyle}
                  formatter={(value) => [`${value}%`, 'Conversion rate']}
                />
                <Area
                  type="monotone"
                  dataKey="conversion_rate"
                  name="Conversion rate"
                  stroke="#8069ed"
                  strokeWidth={2.5}
                  fill="url(#conversionFill)"
                  activeDot={{ r: 5, stroke: '#fff', strokeWidth: 2, fill: '#8069ed' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </article>

        <article className="surface-card min-w-0 p-4 sm:p-5 xl:col-span-3">
          <div className="mb-4 flex items-start gap-3">
            <div className="rounded-xl bg-[#edf2ff] p-2.5 text-[#5c76dc]">
              <BriefcaseBusiness className="h-4 w-4" />
            </div>
            <div>
              <h2 className="section-heading">Lead sources</h2>
              <p className="section-description">Where new opportunities begin</p>
            </div>
          </div>
          <div className="relative mx-auto h-[160px] w-full max-w-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={metrics.leads_by_source}
                  dataKey="count"
                  nameKey="source"
                  cx="50%"
                  cy="50%"
                  innerRadius={51}
                  outerRadius={73}
                  paddingAngle={3}
                  stroke="none"
                >
                  {metrics.leads_by_source.map((source, index) => (
                    <Cell key={source.source} fill={SOURCE_COLORS[index % SOURCE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-[22px] font-bold tracking-tight text-[#202b4d]">{metrics.total_leads}</span>
              <span className="text-[10px] font-medium text-[#8992aa]">Total leads</span>
            </div>
          </div>
          <div className="mt-2 space-y-2">
            {metrics.leads_by_source.map((source, index) => (
              <div key={source.source} className="flex items-center justify-between gap-2 text-[11px]">
                <span className="flex min-w-0 items-center gap-2 text-[#66718e]">
                  <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: SOURCE_COLORS[index % SOURCE_COLORS.length] }} />
                  <span className="truncate">{source.source}</span>
                </span>
                <span className="shrink-0 font-semibold text-[#3b4666]">{source.percentage}%</span>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="grid grid-cols-1 gap-4 xl:grid-cols-12">
        <article className="surface-card min-w-0 p-4 sm:p-5 xl:col-span-5">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="rounded-xl bg-[#f0edff] p-2.5 text-[#7966df]">
                <Bot className="h-4 w-4" />
              </div>
              <div>
                <h2 className="section-heading">Recent agent activity</h2>
                <p className="section-description">Latest actions from your AI sales agent</p>
              </div>
            </div>
            <button type="button" onClick={() => navigate('/agent-runs')} className="mt-1 inline-flex shrink-0 items-center gap-1 text-xs font-semibold text-[#6470d8] transition-colors hover:text-[#454fb8]">
              View all <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
          {metrics.recent_agent_activity.length === 0 ? (
            <div className="flex min-h-[180px] flex-col items-center justify-center rounded-xl bg-[#f8f9fd] px-4 text-center">
              <Bot className="mb-2 h-5 w-5 text-[#9aa4bd]" />
              <p className="text-xs text-[#77819d]">No recent agent runs. Launch a run from the Leads view.</p>
            </div>
          ) : (
            <div className="relative space-y-1 before:absolute before:bottom-5 before:left-[13px] before:top-5 before:w-px before:bg-[#e7e9f4]">
              {metrics.recent_agent_activity.map((activity) => (
                <button
                  type="button"
                  key={activity.id}
                  onClick={() => navigate('/agent-runs')}
                  className="relative flex w-full items-center gap-3 rounded-xl px-1.5 py-3 text-left transition-colors hover:bg-[#f8f9fd]"
                >
                  <span className="relative z-10 flex h-[27px] w-[27px] shrink-0 items-center justify-center rounded-full border-[3px] border-white bg-[#eef0ff] text-[#7167d4] shadow-[0_0_0_1px_#e6e8f4]">
                    {activity.status === 'completed' ? <CheckCircle2 className="h-3.5 w-3.5" /> : activity.status === 'awaiting_approval' ? <Clock3 className="h-3.5 w-3.5" /> : <Sparkles className="h-3.5 w-3.5" />}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-xs font-semibold text-[#303b5c]">{activity.action}</span>
                    <span className="mt-0.5 block truncate text-[11px] text-[#818ba5]">{activity.lead_name} · {activity.company}</span>
                  </span>
                  <span className="flex shrink-0 flex-col items-end gap-1">
                    <Badge variant={getStatusVariant(activity.status)} size="sm" className="text-[9px]">
                      {formatStatus(activity.status)}
                    </Badge>
                    <span className="text-[10px] text-[#969fb5]">{activity.timestamp}</span>
                  </span>
                </button>
              ))}
            </div>
          )}
        </article>

        <article className="surface-card min-w-0 p-4 sm:p-5 xl:col-span-7">
          <div className="mb-4 flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="rounded-xl bg-[#fff1ef] p-2.5 text-[#e57871]">
                <AlertCircle className="h-4 w-4" />
              </div>
              <div>
                <h2 className="section-heading">Leads needing attention</h2>
                <p className="section-description">Prioritized from current lead analysis and follow-up signals</p>
              </div>
            </div>
            <button type="button" onClick={() => navigate('/leads')} className="mt-1 inline-flex shrink-0 items-center gap-1 text-xs font-semibold text-[#6470d8] transition-colors hover:text-[#454fb8]">
              All leads <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>

          {strongestSignal && (
            <button
              type="button"
              onClick={() => navigate(`/leads/${strongestSignal.id}`)}
              className="mb-3 flex w-full items-center gap-3 rounded-xl border border-[#e5e5fb] bg-[linear-gradient(100deg,#f7f6ff,#f2f6ff)] p-3 text-left transition-colors hover:border-[#d1d1f3]"
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white text-[#7668db] shadow-sm">
                <ArrowUpRight className="h-4 w-4" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-[10px] font-semibold uppercase tracking-[0.1em] text-[#8287b9]">Strongest conversion signal</span>
                <span className="mt-0.5 block truncate text-xs font-semibold text-[#303b5c]">{strongestSignal.name} <span className="font-normal text-[#818ba5]">· {strongestSignal.company}</span></span>
              </span>
              <span className="shrink-0 text-sm font-bold text-[#625fc6]">{Math.round(strongestSignal.conversion_probability * 100)}%</span>
            </button>
          )}

          {metrics.leads_needing_attention.length === 0 ? (
            <div className="flex min-h-[140px] flex-col items-center justify-center rounded-xl bg-[#f8f9fd] px-4 text-center">
              <CheckCircle2 className="mb-2 h-5 w-5 text-emerald-500" />
              <p className="text-xs text-[#77819d]">All lead follow-ups are currently on schedule.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[510px] text-left">
                <thead>
                  <tr className="border-b border-[#edf0f6] text-[10px] font-semibold uppercase tracking-[0.1em] text-[#929bb2]">
                    <th className="pb-2.5 pl-2">Lead</th>
                    <th className="pb-2.5">Priority</th>
                    <th className="pb-2.5">Win likelihood</th>
                    <th className="pb-2.5 text-right">Signal</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#f0f1f7]">
                  {metrics.leads_needing_attention.map((lead) => (
                    <tr
                      key={lead.id}
                      onClick={() => navigate(`/leads/${lead.id}`)}
                      className="cursor-pointer transition-colors hover:bg-[#fafaff]"
                    >
                      <td className="py-3 pl-2 pr-3">
                        <span className="block text-xs font-semibold text-[#303b5c]">{lead.name}</span>
                        <span className="mt-0.5 block text-[10px] text-[#858fa8]">{lead.company} · {lead.sales_stage}</span>
                      </td>
                      <td className="py-3 pr-3">
                        <Badge variant={lead.priority_category === 'high' ? 'danger' : lead.priority_category === 'medium' ? 'warning' : 'info'} size="sm">
                          {lead.priority_category} · {lead.priority_score}
                        </Badge>
                      </td>
                      <td className="py-3 pr-3">
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 w-14 overflow-hidden rounded-full bg-[#eef0f6]">
                            <div className="h-full rounded-full bg-gradient-to-r from-[#7569e7] to-[#4c9dea]" style={{ width: `${Math.min(100, Math.max(0, lead.conversion_probability * 100))}%` }} />
                          </div>
                          <span className="text-[11px] font-semibold text-[#465170]">{Math.round(lead.conversion_probability * 100)}%</span>
                        </div>
                      </td>
                      <td className="max-w-[150px] py-3 text-right text-[10px] leading-4 text-[#818ba5]">{lead.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>
      </section>

      <div className="flex flex-wrap items-center justify-between gap-2 px-1 pb-1 text-[10px] text-[#929bb2]">
        <span>Open pipeline: <span className="font-semibold text-[#65708e]">{metrics.open_pipeline_count}</span></span>
        <span className="inline-flex items-center gap-1"><Clock3 className="h-3 w-3" /> Analytics are refreshed automatically</span>
      </div>
    </div>
  );
};
