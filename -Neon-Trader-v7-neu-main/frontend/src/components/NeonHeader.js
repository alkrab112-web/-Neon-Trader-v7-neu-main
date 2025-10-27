import React, { useContext, useState } from 'react';
import { AppContext } from '../App';
import { 
  User, Settings, LogOut, Power, Wifi, WifiOff, 
  Shield, Bell, Menu, X, Activity
} from 'lucide-react';

const NeonHeader = () => {
  const context = useContext(AppContext);
  const { currentUser, logout, isLocked, setIsLocked } = context || {};
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('connected'); // connected, disconnected, syncing

  const handleLogout = () => {
    if (logout) {
      logout();
    }
    setShowUserMenu(false);
  };

  const togglePowerMode = () => {
    if (setIsLocked) {
      setIsLocked(!isLocked);
    }
    // In real implementation, this would change trading mode
  };

  const getConnectionIcon = () => {
    switch (connectionStatus) {
      case 'connected':
        return <Wifi className="text-green-400 status-connected" size={18} />;
      case 'disconnected':
        return <WifiOff className="text-red-400 status-disconnected" size={18} />;
      case 'syncing':
        return <Activity className="text-yellow-400 status-syncing" size={18} />;
      default:
        return <Wifi className="text-gray-400" size={18} />;
    }
  };

  const getPowerStatus = () => {
    if (!isLocked) {
      return {
        class: 'power-on',
        text: 'نشط',
        icon: '🟢'
      };
    }
    return {
      class: 'power-off', 
      text: 'مقفل',
      icon: '🔴'
    };
  };

  return (
    <header className="glass-card border-b border-cyan-500/20 sticky top-0 z-50 backdrop-blur-xl ml-64">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo and Brand */}
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="w-10 h-10 rounded-full bg-gradient-to-r from-cyan-500 to-blue-500 flex items-center justify-center font-bold text-white shadow-lg">
                N7
              </div>
              <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-400 rounded-full animate-pulse shadow-lg shadow-green-400/50"></div>
            </div>
            
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                نيون تريدر V7
              </h1>
              <p className="text-xs text-gray-400">منصة التداول الذكية الآمنة</p>
            </div>
          </div>

          {/* Center - Connection Status and Power */}
          <div className="hidden md:flex items-center gap-6">
            {/* Connection Status */}
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-800/50 border border-gray-700/50">
              {getConnectionIcon()}
              <span className="text-sm text-gray-300">
                {connectionStatus === 'connected' && 'متصل'}
                {connectionStatus === 'disconnected' && 'غير متصل'}
                {connectionStatus === 'syncing' && 'يتصل...'}
              </span>
            </div>

            {/* Power Mode Toggle */}
            <button
              onClick={togglePowerMode}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all transform hover:scale-105 ${
                !isLocked 
                  ? 'bg-green-500/20 border border-green-500/50 text-green-400' 
                  : 'bg-red-500/20 border border-red-500/50 text-red-400'
              }`}
            >
              <div className={`power-indicator ${getPowerStatus().class}`}></div>
              <Power size={16} />
              <span className="text-sm font-medium">{getPowerStatus().text}</span>
            </button>
          </div>

          {/* Right Side - User Info and Actions */}
          <div className="flex items-center gap-4">
            {/* Notifications */}
            <button className="relative p-2 rounded-lg bg-gray-800/50 hover:bg-gray-700/50 transition-all border border-gray-700/50">
              <Bell size={18} className="text-gray-400" />
              <div className="absolute -top-1 -right-1 w-2 h-2 bg-cyan-400 rounded-full animate-pulse"></div>
            </button>

            {/* Security Shield */}
            <div className="hidden md:flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-800/50 border border-gray-700/50">
              <Shield size={16} className="text-cyan-400" />
              <span className="text-xs text-gray-300">آمن</span>
            </div>

            {/* User Menu */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-3 px-4 py-2 rounded-lg bg-gray-800/50 hover:bg-gray-700/50 transition-all border border-gray-700/50"
              >
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-cyan-500 to-purple-500 flex items-center justify-center text-white font-semibold text-sm">
                    {currentUser?.username?.charAt(0)?.toUpperCase() || 'U'}
                  </div>
                  <div className="hidden md:block text-right">
                    <div className="text-sm font-medium text-white">
                      {currentUser?.username || 'مستخدم'}
                    </div>
                    <div className="text-xs text-gray-400">
                      {currentUser?.email || 'email@example.com'}
                    </div>
                  </div>
                </div>
                <Menu size={16} className="text-gray-400" />
              </button>

              {/* User Dropdown Menu */}
              {showUserMenu && (
                <div className="absolute left-0 mt-2 w-64 glass-card border border-cyan-500/30 shadow-2xl shadow-cyan-500/20 z-50 fade-in">
                  <div className="p-4 border-b border-gray-700/50">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-full bg-gradient-to-r from-cyan-500 to-purple-500 flex items-center justify-center text-white font-bold">
                        {currentUser?.username?.charAt(0)?.toUpperCase() || 'U'}
                      </div>
                      <div>
                        <div className="font-semibold text-white">
                          {currentUser?.username || 'مستخدم'}
                        </div>
                        <div className="text-sm text-gray-400">
                          {currentUser?.email || 'email@example.com'}
                        </div>
                        <div className="text-xs text-cyan-400 mt-1">
                          معرف: {currentUser?.id?.substring(0, 8) || 'xxxxxxxx'}...
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="p-2">
                    <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-800/50 text-gray-300 hover:text-white transition-all">
                      <User size={16} />
                      <span>الملف الشخصي</span>
                    </button>
                    
                    <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-800/50 text-gray-300 hover:text-white transition-all">
                      <Settings size={16} />
                      <span>الإعدادات</span>
                    </button>
                    
                    <button className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-gray-800/50 text-gray-300 hover:text-white transition-all">
                      <Shield size={16} />
                      <span>الأمان</span>
                    </button>
                    
                    <div className="border-t border-gray-700/50 my-2"></div>
                    
                    <button 
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-red-500/20 text-red-400 hover:text-red-300 transition-all"
                    >
                      <LogOut size={16} />
                      <span>تسجيل الخروج</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Mobile Power Status */}
        <div className="md:hidden mt-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {getConnectionIcon()}
              <span className="text-sm text-gray-300">
                {connectionStatus === 'connected' && 'متصل'}
                {connectionStatus === 'disconnected' && 'غير متصل'}
                {connectionStatus === 'syncing' && 'يتصل...'}
              </span>
            </div>

            <button
              onClick={togglePowerMode}
              className={`flex items-center gap-2 px-3 py-1 rounded-lg transition-all ${
                !isLocked 
                  ? 'bg-green-500/20 border border-green-500/50 text-green-400' 
                  : 'bg-red-500/20 border border-red-500/50 text-red-400'
              }`}
            >
              <div className={`power-indicator ${getPowerStatus().class}`}></div>
              <span className="text-xs font-medium">{getPowerStatus().text}</span>
            </button>
          </div>

          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-gray-800/50 border border-gray-700/50">
            <Shield size={14} className="text-cyan-400" />
            <span className="text-xs text-gray-300">آمن</span>
          </div>
        </div>
      </div>

      {/* Click outside to close menu */}
      {showUserMenu && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setShowUserMenu(false)}
        />
      )}
    </header>
  );
};

export default NeonHeader;