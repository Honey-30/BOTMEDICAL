import React from 'react'
import { useAuth } from '../../store/AuthContext'
import { BellIcon, SearchIcon, UserIcon } from 'lucide-react'

const Header = () => {
  const { user, logout } = useAuth()

  return (
    <header className="bg-white shadow-sm border-b border-secondary-200 px-6 py-4">
      <div className="flex items-center justify-between">
        {/* Search bar */}
        <div className="flex-1 max-w-2xl">
          <div className="relative">
            <SearchIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-secondary-400" />
            <input
              type="text"
              placeholder="Search projects, tasks, or ask AI..."
              className="w-full pl-10 pr-4 py-2 border border-secondary-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Notifications */}
          <button className="relative p-2 text-secondary-400 hover:text-secondary-600 transition-colors">
            <BellIcon className="w-6 h-6" />
            <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
          </button>

          {/* User menu */}
          <div className="relative group">
            <button className="flex items-center space-x-3 p-2 rounded-lg hover:bg-secondary-100 transition-colors">
              <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                <UserIcon className="w-5 h-5 text-white" />
              </div>
              <div className="text-left">
                <div className="text-sm font-medium text-secondary-900">
                  {user?.full_name || user?.username}
                </div>
                <div className="text-xs text-secondary-500">{user?.role}</div>
              </div>
            </button>

            {/* Dropdown menu */}
            <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-secondary-200 py-1 opacity-0 group-hover:opacity-100 transition-opacity z-50">
              <a href="/profile" className="block px-4 py-2 text-sm text-secondary-700 hover:bg-secondary-100">
                Profile
              </a>
              <a href="/settings" className="block px-4 py-2 text-sm text-secondary-700 hover:bg-secondary-100">
                Settings
              </a>
              <hr className="my-1 border-secondary-200" />
              <button
                onClick={logout}
                className="block w-full text-left px-4 py-2 text-sm text-red-700 hover:bg-red-50"
              >
                Sign out
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default Header