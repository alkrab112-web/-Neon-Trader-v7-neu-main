import React, { useContext } from 'react';
import { AppContext } from '../App';
import { 
  Home, Layers, Bot, Settings, Wrench, Bell, 
  TrendingUp, BarChart3, Shield, Activity
} from 'lucide-react';

const NeonNavigation = () => {
  const { currentPage, setCurrentPage } = useContext(AppContext);

  const navItems = [
    {
      id: 'home',
      name: 'الرئيسية',
      icon: Home,
      color: 'cyan',
      gradient: 'from-cyan-500 to-blue-500',
      description: 'لوحة التداول الرئيسية'
    },
    {
      id: 'platforms',
      name: 'المنصات',
      icon: Layers,
      color: 'purple',
      gradient: 'from-purple-500 to-pink-500',
      description: 'إدارة منصات التداول'
    },
    {
      id: 'tools',
      name: 'أدوات التداول',
      icon: Wrench,
      color: 'emerald',
      gradient: 'from-emerald-500 to-teal-500',
      description: 'أدوات التحليل الفني'
    },
    {
      id: 'assistant',
      name: 'المساعد الذكي',
      icon: Bot,
      color: 'orange',
      gradient: 'from-orange-500 to-red-500',
      description: 'مساعد ذكي للتداول'
    },
    {
      id: 'notifications',
      name: 'الإشعارات',
      icon: Bell,
      color: 'yellow',
      gradient: 'from-yellow-500 to-orange-500',
      description: 'إشعارات السوق'
    },
    {
      id: 'settings',
      name: 'الإعدادات',
      icon: Settings,
      color: 'gray',
      gradient: 'from-gray-500 to-slate-500',
      description: 'إعدادات التطبيق'
    }
  ];

  const handleNavClick = (pageId) => {
    setCurrentPage(pageId);
  };

  return (
    <nav className="glass-card border-r border-cyan-500/20 min-h-screen w-64 p-4 backdrop-blur-xl">
      {/* Navigation Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <TrendingUp className="text-cyan-400 neon-glow-cyan" size={20} />
          <h2 className="font-bold text-white">لوحة التنقل</h2>
        </div>
        <p className="text-gray-400 text-sm">منصة التداول الذكية</p>
      </div>

      {/* Navigation Items */}
      <div className="space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentPage === item.id;
          
          return (
            <button
              key={item.id}
              onClick={() => handleNavClick(item.id)}
              className={`w-full group relative flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 ${
                isActive
                  ? `bg-gradient-to-r ${item.gradient} text-white shadow-lg shadow-${item.color}-500/30 nav-item active`
                  : 'nav-item text-gray-400 hover:text-white hover:bg-gray-800/50'
              }`}
            >
              {/* Active Indicator */}
              {isActive && (
                <div className={`absolute right-0 top-1/2 transform -translate-y-1/2 w-1 h-8 bg-${item.color}-400 rounded-l-full`} />
              )}
              
              {/* Icon */}
              <Icon 
                size={20} 
                className={`transition-all duration-300 ${
                  isActive 
                    ? 'text-white scale-110' 
                    : `text-${item.color}-400 group-hover:scale-105`
                }`} 
              />
              
              {/* Text Content */}
              <div className="flex-1 text-right">
                <div className={`font-semibold transition-colors ${
                  isActive ? 'text-white' : 'text-gray-300'
                }`}>
                  {item.name}
                </div>
                <div className={`text-xs transition-colors ${
                  isActive ? 'text-white/80' : 'text-gray-500'
                }`}>
                  {item.description}
                </div>
              </div>

              {/* Hover Glow Effect */}
              {!isActive && (
                <div className={`absolute inset-0 bg-gradient-to-r ${item.gradient} opacity-0 group-hover:opacity-10 rounded-xl transition-opacity duration-300`} />
              )}
            </button>
          );
        })}
      </div>

      {/* Bottom Section - System Status */}
      <div className="mt-auto pt-8">
        <div className="glass-card-hover p-4 rounded-xl bg-gray-800/30 border border-gray-700/50">
          <div className="flex items-center gap-3 mb-3">
            <Activity className="text-green-400 animate-pulse" size={16} />
            <span className="text-sm font-semibold text-white">حالة النظام</span>
          </div>
          
          <div className="space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-400">الخادم</span>
              <span className="text-green-400 flex items-center gap-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                نشط
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-400">قاعدة البيانات</span>
              <span className="text-green-400 flex items-center gap-1">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                متصل
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-gray-400">الذكاء الصناعي</span>
              <span className="text-cyan-400 flex items-center gap-1">
                <div className="w-2 h-2 bg-cyan-400 rounded-full animate-pulse" />
                جاهز
              </span>
            </div>
          </div>
        </div>

        {/* Security Badge */}
        <div className="mt-4 flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-gradient-to-r from-green-500/20 to-cyan-500/20 border border-green-500/30">
          <Shield className="text-green-400" size={16} />
          <span className="text-sm font-semibold text-green-400">محمي بـ SSL</span>
        </div>
      </div>
    </nav>
  );
};

export default NeonNavigation;