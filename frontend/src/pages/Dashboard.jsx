import React from 'react'
import { useQuery } from 'react-query'
import { apiService } from '../services/api'
import LoadingSpinner from '../components/UI/LoadingSpinner'
import {
  FolderIcon,
  CheckSquareIcon,
  ClockIcon,
  TrendingUpIcon,
  AlertTriangleIcon,
  PlusIcon
} from 'lucide-react'

const Dashboard = () => {
  const { data: analytics, isLoading } = useQuery(
    'overview-analytics',
    apiService.getOverviewAnalytics
  )

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  const stats = [
    {
      name: 'Total Projects',
      value: analytics?.project_analytics?.total_projects || 0,
      icon: FolderIcon,
      color: 'bg-blue-500',
      change: '+12%',
      changeType: 'positive'
    },
    {
      name: 'Active Tasks',
      value: analytics?.task_analytics?.total_tasks - analytics?.task_analytics?.completed_tasks || 0,
      icon: CheckSquareIcon,
      color: 'bg-green-500',
      change: '+8%',
      changeType: 'positive'
    },
    {
      name: 'Completion Rate',
      value: `${Math.round(analytics?.task_analytics?.completion_rate || 0)}%`,
      icon: TrendingUpIcon,
      color: 'bg-purple-500',
      change: '+5%',
      changeType: 'positive'
    },
    {
      name: 'Overdue Tasks',
      value: analytics?.task_analytics?.overdue_tasks || 0,
      icon: AlertTriangleIcon,
      color: 'bg-red-500',
      change: '-2%',
      changeType: 'negative'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-secondary-900">Dashboard</h1>
          <p className="text-secondary-600 mt-1">
            Welcome back! Here's an overview of your projects and tasks.
          </p>
        </div>
        
        <div className="flex space-x-3">
          <button className="btn-secondary">
            <ClockIcon className="w-4 h-4 mr-2" />
            View Recent
          </button>
          <button className="btn-primary">
            <PlusIcon className="w-4 h-4 mr-2" />
            New Project
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon
          return (
            <div key={stat.name} className="card">
              <div className="flex items-center">
                <div className={`p-3 rounded-lg ${stat.color}`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-secondary-600">{stat.name}</p>
                  <div className="flex items-baseline">
                    <p className="text-2xl font-semibold text-secondary-900">{stat.value}</p>
                    <span className={`ml-2 text-sm font-medium ${
                      stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {stat.change}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Projects */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-secondary-900">Recent Projects</h3>
            <button className="text-primary-600 hover:text-primary-500 text-sm font-medium">
              View all
            </button>
          </div>
          
          <div className="space-y-3">
            {[1, 2, 3].map((item) => (
              <div key={item} className="flex items-center justify-between p-3 bg-secondary-50 rounded-lg">
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                    <FolderIcon className="w-5 h-5 text-primary-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-secondary-900">Project {item}</p>
                    <p className="text-xs text-secondary-500">Updated 2 hours ago</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-secondary-900">85%</p>
                  <p className="text-xs text-secondary-500">Complete</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Task Activity */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-secondary-900">Task Activity</h3>
            <button className="text-primary-600 hover:text-primary-500 text-sm font-medium">
              View all
            </button>
          </div>
          
          <div className="space-y-3">
            {[
              { action: 'Task completed', task: 'Design mockups', time: '2 minutes ago' },
              { action: 'New task created', task: 'Setup database', time: '1 hour ago' },
              { action: 'Task assigned', task: 'Write documentation', time: '3 hours ago' }
            ].map((activity, index) => (
              <div key={index} className="flex items-start">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <CheckSquareIcon className="w-4 h-4 text-green-600" />
                </div>
                <div className="ml-3 flex-1">
                  <p className="text-sm text-secondary-900">
                    <span className="font-medium">{activity.action}:</span> {activity.task}
                  </p>
                  <p className="text-xs text-secondary-500">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* AI Insights */}
      <div className="card">
        <h3 className="text-lg font-semibold text-secondary-900 mb-4">AI Insights</h3>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white text-sm font-medium">AI</span>
              </div>
            </div>
            <div className="ml-3">
              <h4 className="text-sm font-medium text-blue-900">
                Productivity Insight
              </h4>
              <p className="text-sm text-blue-700 mt-1">
                You've completed {analytics?.productivity_metrics?.tasks_completed_this_week || 0} tasks this week, 
                which is {analytics?.productivity_metrics?.productivity_trend || 'stable'} compared to last week. 
                Consider prioritizing the 3 overdue tasks to improve your completion rate.
              </p>
              <button className="mt-2 text-blue-600 hover:text-blue-500 text-sm font-medium">
                Get suggestions →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Dashboard