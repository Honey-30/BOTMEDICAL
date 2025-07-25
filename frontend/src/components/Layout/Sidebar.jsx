import React, { useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { 
  HomeIcon, 
  FolderIcon, 
  CheckSquareIcon, 
  BarChart3Icon,
  MessageSquareIcon,
  SettingsIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from 'lucide-react'
import clsx from 'clsx'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Projects', href: '/projects', icon: FolderIcon },
  { name: 'Tasks', href: '/tasks', icon: CheckSquareIcon },
  { name: 'Analytics', href: '/analytics', icon: BarChart3Icon },
  { name: 'AI Assistant', href: '/ai-chat', icon: MessageSquareIcon },
  { name: 'Settings', href: '/settings', icon: SettingsIcon },
]

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  return (
    <div className={clsx(
      'bg-white shadow-lg transition-all duration-300 flex flex-col',
      collapsed ? 'w-16' : 'w-64'
    )}>
      {/* Logo and collapse button */}
      <div className="flex items-center justify-between p-4 border-b border-secondary-200">
        <div className={clsx(
          'flex items-center transition-opacity duration-300',
          collapsed ? 'opacity-0' : 'opacity-100'
        )}>
          <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">AI</span>
          </div>
          <span className="ml-2 text-lg font-semibold text-secondary-900">
            Project Manager
          </span>
        </div>
        
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-1 rounded-md hover:bg-secondary-100 transition-colors"
        >
          {collapsed ? (
            <ChevronRightIcon className="w-5 h-5 text-secondary-600" />
          ) : (
            <ChevronLeftIcon className="w-5 h-5 text-secondary-600" />
          )}
        </button>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navigation.map((item) => {
          const isActive = location.pathname === item.href
          const Icon = item.icon
          
          return (
            <NavLink
              key={item.name}
              to={item.href}
              className={clsx(
                'flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                'group relative',
                isActive
                  ? 'bg-primary-100 text-primary-700'
                  : 'text-secondary-600 hover:bg-secondary-100 hover:text-secondary-900'
              )}
            >
              <Icon className={clsx(
                'flex-shrink-0 w-5 h-5',
                isActive ? 'text-primary-500' : 'text-secondary-400'
              )} />
              
              <span className={clsx(
                'ml-3 transition-opacity duration-300',
                collapsed ? 'opacity-0' : 'opacity-100'
              )}>
                {item.name}
              </span>

              {/* Tooltip for collapsed state */}
              {collapsed && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-secondary-900 text-white text-xs rounded-md opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-50">
                  {item.name}
                </div>
              )}
            </NavLink>
          )
        })}
      </nav>

      {/* User info (collapsed state) */}
      {collapsed && (
        <div className="p-4 border-t border-secondary-200">
          <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
            <span className="text-white text-xs font-medium">U</span>
          </div>
        </div>
      )}
    </div>
  )
}

export default Sidebar