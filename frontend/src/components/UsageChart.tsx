"use client";

import { useState } from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

interface AnalyticsData {
  period: string;
  granularity: string;
  data_points: Array<{
    timestamp: string;
    count: number;
    call_types: Record<string, number>;
  }>;
  total_calls: number;
  rpm_peak: number;
  rpd_average: number;
  breakdown_by_type: Record<string, number>;
}

interface UsageChartProps {
  data: AnalyticsData | null;
  isLoading: boolean;
  onPeriodChange: (period: "24h" | "7d" | "30d" | "all") => void;
  currentPeriod: "24h" | "7d" | "30d" | "all";
}

export default function UsageChart({
  data,
  isLoading,
  onPeriodChange,
  currentPeriod,
}: UsageChartProps) {
  const [chartType, setChartType] = useState<"line" | "bar">("line");

  // Format timestamp for display
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    if (data?.granularity === "hourly") {
      return date.toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        hour: "numeric",
      });
    }
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  // Transform data for recharts
  const chartData = data?.data_points.map((point) => ({
    name: formatTimestamp(point.timestamp),
    total: point.count,
    generation: point.call_types.generation || 0,
    edit: point.call_types.edit || 0,
    question: point.call_types.question || 0,
  })) || [];

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900 mb-2">{label}</p>
          <div className="space-y-1">
            <p className="text-sm text-gray-600">
              Total: <span className="font-semibold">{payload[0].payload.total}</span>
            </p>
            {payload[0].payload.generation > 0 && (
              <p className="text-sm text-blue-600">
                Generation: <span className="font-semibold">{payload[0].payload.generation}</span>
              </p>
            )}
            {payload[0].payload.edit > 0 && (
              <p className="text-sm text-green-600">
                Edit: <span className="font-semibold">{payload[0].payload.edit}</span>
              </p>
            )}
            {payload[0].payload.question > 0 && (
              <p className="text-sm text-purple-600">
                Question: <span className="font-semibold">{payload[0].payload.question}</span>
              </p>
            )}
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Usage Analytics</h2>
        <div className="flex items-center gap-2">
          {/* Chart Type Toggle */}
          <div className="flex items-center bg-gray-100 rounded-md p-1">
            <button
              onClick={() => setChartType("line")}
              className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                chartType === "line"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Line
            </button>
            <button
              onClick={() => setChartType("bar")}
              className={`px-3 py-1 text-xs font-medium rounded transition-colors ${
                chartType === "bar"
                  ? "bg-white text-gray-900 shadow-sm"
                  : "text-gray-600 hover:text-gray-900"
              }`}
            >
              Bar
            </button>
          </div>
        </div>
      </div>

      {/* Period Filters */}
      <div className="flex items-center gap-2 mb-6 overflow-x-auto">
        {(["24h", "7d", "30d", "all"] as const).map((period) => (
          <button
            key={period}
            onClick={() => onPeriodChange(period)}
            className={`px-4 py-2 text-sm font-medium rounded-md whitespace-nowrap transition-colors ${
              currentPeriod === period
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            {period === "24h" && "Last 24 Hours"}
            {period === "7d" && "Last 7 Days"}
            {period === "30d" && "Last 30 Days"}
            {period === "all" && "All Time"}
          </button>
        ))}
      </div>

      {/* Stats Summary */}
      {data && !isLoading && (
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-xs font-medium text-gray-600 mb-1">Total Calls</p>
            <p className="text-2xl font-bold text-gray-900">{data.total_calls}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-xs font-medium text-gray-600 mb-1">Peak RPM</p>
            <p className="text-2xl font-bold text-gray-900">{data.rpm_peak}</p>
          </div>
          <div className="bg-gray-50 rounded-lg p-4">
            <p className="text-xs font-medium text-gray-600 mb-1">Avg RPD</p>
            <p className="text-2xl font-bold text-gray-900">{data.rpd_average}</p>
          </div>
        </div>
      )}

      {/* Chart */}
      <div className="h-80">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading analytics...</p>
            </div>
          </div>
        ) : chartData.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
              <p className="mt-4 text-gray-600">No usage data available for this period</p>
              <p className="text-sm text-gray-500 mt-2">
                Start generating websites to see your analytics
              </p>
            </div>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            {chartType === "line" ? (
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="name"
                  stroke="#6b7280"
                  style={{ fontSize: "12px" }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis stroke="#6b7280" style={{ fontSize: "12px" }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: "12px" }} />
                <Line
                  type="monotone"
                  dataKey="generation"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Generation"
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="edit"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Edit"
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
                <Line
                  type="monotone"
                  dataKey="question"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  name="Question"
                  dot={{ r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            ) : (
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis
                  dataKey="name"
                  stroke="#6b7280"
                  style={{ fontSize: "12px" }}
                  angle={-45}
                  textAnchor="end"
                  height={80}
                />
                <YAxis stroke="#6b7280" style={{ fontSize: "12px" }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: "12px" }} />
                <Bar dataKey="generation" fill="#3b82f6" name="Generation" />
                <Bar dataKey="edit" fill="#10b981" name="Edit" />
                <Bar dataKey="question" fill="#8b5cf6" name="Question" />
              </BarChart>
            )}
          </ResponsiveContainer>
        )}
      </div>

      {/* Breakdown by Type */}
      {data && !isLoading && data.total_calls > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Breakdown by Type</h3>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(data.breakdown_by_type).map(([type, count]) => {
              const percentage = ((count / data.total_calls) * 100).toFixed(1);
              const colors: Record<string, { bg: string; text: string }> = {
                generation: { bg: "bg-blue-100", text: "text-blue-900" },
                edit: { bg: "bg-green-100", text: "text-green-900" },
                question: { bg: "bg-purple-100", text: "text-purple-900" },
              };
              const color = colors[type] || { bg: "bg-gray-100", text: "text-gray-900" };

              return (
                <div key={type} className={`${color.bg} rounded-lg p-3`}>
                  <p className={`text-xs font-medium ${color.text} mb-1 capitalize`}>{type}</p>
                  <div className="flex items-baseline gap-2">
                    <p className={`text-xl font-bold ${color.text}`}>{count}</p>
                    <p className={`text-xs ${color.text} opacity-75`}>({percentage}%)</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
