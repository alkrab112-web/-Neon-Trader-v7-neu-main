import React, { useState, useContext, useEffect } from 'react';
import { AppContext } from '../App';
import { 
  Settings, Shield, Bell, Globe, Palette, Key,
  Smartphone, Eye, EyeOff, Save, RefreshCw,
  AlertTriangle, CheckCircle, Lock, Unlock,
  Moon, Sun, Languages, Volume, VolumeX, TrendingUp
} from 'lucide-react';
import TwoFactorAuth from './TwoFactorAuth';
import axios from 'axios';

const EnhancedSettings = () => {
  const { showToast, currentUser, settings, updateSettings } = useContext(AppContext);
  const [activeSection, setActiveSection] = useState('security');
  const [show2FASetup, setShow2FASetup] = useState(false);
  const [loading, setLoading] = useState({});
  const [localSettings, setLocalSettings] = useState(settings || {});

  // Settings sections
  const sections = [
    {
      id: 'security',
      name: 'الأمان',
      icon: Shield,
      color: 'from-red-500 to-red-600'
    },
    {
      id: 'notifications',
      name: 'الإشعارات',
      icon: Bell,
      color: 'from-yellow-500 to-orange-500'
    },
    {
      id: 'trading',
      name: 'التداول',
      icon: TrendingUp,
      color: 'from-green-500 to-emerald-500'
    },
    {
      id: 'appearance',
      name: 'المظهر',
      icon: Palette,
      color: 'from-purple-500 to-pink-500'
    },
    {
      id: 'general',
      name: 'عام',
      icon: Settings,
      color: 'from-cyan-500 to-blue-500'
    }
  ];

  const updateLocalSetting = (section: string, key: string, value: any) => {
    setLocalSettings(prev => ({
      ...prev,
      [section]: {
        ...prev[section],
        [key]: value
      }
    }));
  };

  const saveSettings = async (section?: string) => {
    try {
      const sectionKey = section || activeSection;
      setLoading(prev => ({ ...prev, [sectionKey]: true }));
      
      await updateSettings(localSettings);
      showToast('تم حفظ الإعدادات بنجاح', 'success');
    } catch (error) {
      showToast('فشل في حفظ الإعدادات', 'error');
    } finally {
      setLoading(prev => ({ ...prev, [section || activeSection]: false }));
    }
  };

  const disable2FA = async () => {
    const password = prompt('أدخل كلمة المرور لتأكيد إلغاء المصادقة الثنائية:');
    if (!password) return;

    try {
      setLoading(prev => ({ ...prev, '2fa_disable': true }));
      
      const formData = new FormData();
      formData.append('password', password);
      
      await axios.post('/api/auth/2fa/disable', formData);
      showToast('تم إلغاء تفعيل المصادقة الثنائية', 'success');
      
      // Update user state
      // currentUser.two_factor_enabled = false; // Update in context
      
    } catch (error) {
      showToast('فشل في إلغاء المصادقة الثنائية', 'error');
    } finally {
      setLoading(prev => ({ ...prev, '2fa_disable': false }));
    }
  };

  const regenerateBackupCodes = async () => {
    try {
      setLoading(prev => ({ ...prev, 'backup_codes': true }));
      const response = await axios.get('/api/auth/2fa/backup-codes');
      
      // Show backup codes in modal or download
      const codes = response.data.backup_codes.join('\n');
      const blob = new Blob([codes], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `backup-codes-${Date.now()}.txt`;
      a.click();
      URL.revokeObjectURL(url);
      
      showToast('تم إنشاء رموز احتياطية جديدة', 'success');
    } catch (error) {
      showToast('فشل في إنشاء رموز احتياطية', 'error');
    } finally {
      setLoading(prev => ({ ...prev, 'backup_codes': false }));
    }
  };

  // Render Security Settings
  const renderSecuritySettings = () => (
    <div className="space-y-6">
      <div className="glass-card p-6 border-l-4 border-red-400">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
          <Shield className="text-red-400" size={24} />
          إعدادات الأمان
        </h3>

        {/* Two-Factor Authentication */}
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
            <div className="flex items-center gap-3">
              <Smartphone className="text-cyan-400" size={20} />
              <div>
                <h4 className="font-semibold text-white">المصادقة الثنائية</h4>
                <p className="text-sm text-gray-400">
                  {currentUser?.two_factor_enabled 
                    ? 'نشطة - حسابك محمي بمصادقة ثنائية'
                    : 'غير نشطة - ننصح بتفعيلها لحماية أفضل'
                  }
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {currentUser?.two_factor_enabled ? (
                <>
                  <div className="flex items-center gap-2 text-green-400 text-sm">
                    <CheckCircle size={16} />
                    مُفعّلة
                  </div>
                  <button
                    onClick={disable2FA}
                    disabled={loading['2fa_disable']}
                    className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-lg text-sm transition-colors disabled:opacity-50"
                  >
                    {loading['2fa_disable'] ? 'جاري الإلغاء...' : 'إلغاء'}
                  </button>
                </>
              ) : (
                <button
                  onClick={() => setShow2FASetup(true)}
                  className="neon-button bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white px-4 py-2 rounded-lg text-sm"
                >
                  تفعيل
                </button>
              )}
            </div>
          </div>

          {/* Backup Codes */}
          {currentUser?.two_factor_enabled && (
            <div className="flex items-center justify-between p-4 bg-gray-800/50 rounded-lg">
              <div className="flex items-center gap-3">
                <Key className="text-yellow-400" size={20} />
                <div>
                  <h4 className="font-semibold text-white">رموز الطوارئ</h4>
                  <p className="text-sm text-gray-400">إنشاء رموز احتياطية جديدة</p>
                </div>
              </div>
              
              <button
                onClick={regenerateBackupCodes}
                disabled={loading['backup_codes']}
                className="bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1 rounded-lg text-sm transition-colors disabled:opacity-50"
              >
                {loading['backup_codes'] ? 'جاري الإنشاء...' : 'إنشاء جديد'}
              </button>
            </div>
          )}

          {/* Session Settings */}
          <div className="p-4 bg-gray-800/50 rounded-lg">
            <div className="flex items-center gap-3 mb-3">
              <Lock className="text-blue-400" size={20} />
              <h4 className="font-semibold text-white">إعدادات الجلسة</h4>
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-300">انتهاء الجلسة التلقائي</span>
                <select
                  value={localSettings.security?.session_timeout || 30}
                  onChange={(e) => updateLocalSetting('security', 'session_timeout', parseInt(e.target.value))}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-white"
                >
                  <option value={15}>15 دقيقة</option>
                  <option value={30}>30 دقيقة</option>
                  <option value={60}>1 ساعة</option>
                  <option value={240}>4 ساعات</option>
                </select>
              </div>
              
              <div className="flex items-center justify-between">
                <span className="text-gray-300">إشعارات تسجيل الدخول</span>
                <button
                  onClick={() => updateLocalSetting('security', 'login_notifications', !localSettings.security?.login_notifications)}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    localSettings.security?.login_notifications 
                      ? 'bg-green-500' 
                      : 'bg-gray-600'
                  }`}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                    localSettings.security?.login_notifications 
                      ? 'translate-x-6' 
                      : 'translate-x-1'
                  }`} />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Render Notifications Settings
  const renderNotificationSettings = () => (
    <div className="space-y-6">
      <div className="glass-card p-6 border-l-4 border-yellow-400">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
          <Bell className="text-yellow-400" size={24} />
          إعدادات الإشعارات
        </h3>

        <div className="space-y-4">
          {/* Email Notifications */}
          <div className="p-4 bg-gray-800/50 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-white">الإشعارات بالبريد الإلكتروني</h4>
              <button
                onClick={() => updateLocalSetting('notifications', 'email', !localSettings.notifications?.email)}
                className={`w-12 h-6 rounded-full transition-colors ${
                  localSettings.notifications?.email ? 'bg-green-500' : 'bg-gray-600'
                }`}
              >
                <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                  localSettings.notifications?.email ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>

          {/* Push Notifications */}
          <div className="p-4 bg-gray-800/50 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-white">الإشعارات الفورية</h4>
              <button
                onClick={() => updateLocalSetting('notifications', 'push', !localSettings.notifications?.push)}
                className={`w-12 h-6 rounded-full transition-colors ${
                  localSettings.notifications?.push ? 'bg-green-500' : 'bg-gray-600'
                }`}
              >
                <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                  localSettings.notifications?.push ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>

          {/* Trading Updates */}
          <div className="p-4 bg-gray-800/50 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-white">تحديثات التداول</h4>
              <button
                onClick={() => updateLocalSetting('notifications', 'trading_updates', !localSettings.notifications?.trading_updates)}
                className={`w-12 h-6 rounded-full transition-colors ${
                  localSettings.notifications?.trading_updates ? 'bg-green-500' : 'bg-gray-600'
                }`}
              >
                <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                  localSettings.notifications?.trading_updates ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>

          {/* Price Alerts */}
          <div className="p-4 bg-gray-800/50 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-white">تنبيهات الأسعار</h4>
              <button
                onClick={() => updateLocalSetting('notifications', 'price_alerts', !localSettings.notifications?.price_alerts)}
                className={`w-12 h-6 rounded-full transition-colors ${
                  localSettings.notifications?.price_alerts ? 'bg-green-500' : 'bg-gray-600'
                }`}
              >
                <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                  localSettings.notifications?.price_alerts ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>

          {/* AI Recommendations */}
          <div className="p-4 bg-gray-800/50 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-white">توصيات الذكاء الصناعي</h4>
              <button
                onClick={() => updateLocalSetting('notifications', 'ai_recommendations', !localSettings.notifications?.ai_recommendations)}
                className={`w-12 h-6 rounded-full transition-colors ${
                  localSettings.notifications?.ai_recommendations ? 'bg-green-500' : 'bg-gray-600'
                }`}
              >
                <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                  localSettings.notifications?.ai_recommendations ? 'translate-x-6' : 'translate-x-1'
                }`} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Render Trading Settings
  const renderTradingSettings = () => (
    <div className="space-y-6">
      <div className="glass-card p-6 border-l-4 border-green-400">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
          <TrendingUp className="text-green-400" size={24} />
          إعدادات التداول
        </h3>

        <div className="space-y-4">
          {/* Risk Management */}
          <div className="p-4 bg-gray-800/50 rounded-lg">
            <h4 className="font-semibold text-white mb-3">إدارة المخاطر</h4>
            
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-300">نسبة المخاطرة الافتراضية</span>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min="1"
                    max="10"
                    value={localSettings.trading?.default_risk_percentage || 2}
                    onChange={(e) => updateLocalSetting('trading', 'default_risk_percentage', parseFloat(e.target.value))}
                    className="w-20"
                  />
                  <span className="text-white w-8 text-center">
                    {localSettings.trading?.default_risk_percentage || 2}%
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-gray-300">وقف الخسارة التلقائي</span>
                <button
                  onClick={() => updateLocalSetting('trading', 'auto_stop_loss', !localSettings.trading?.auto_stop_loss)}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    localSettings.trading?.auto_stop_loss ? 'bg-green-500' : 'bg-gray-600'
                  }`}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                    localSettings.trading?.auto_stop_loss ? 'translate-x-6' : 'translate-x-1'
                  }`} />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-gray-300">وضع التداول الورقي</span>
                <button
                  onClick={() => updateLocalSetting('trading', 'paper_trading_mode', !localSettings.trading?.paper_trading_mode)}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    localSettings.trading?.paper_trading_mode ? 'bg-yellow-500' : 'bg-gray-600'
                  }`}
                >
                  <div className={`w-5 h-5 bg-white rounded-full transition-transform ${
                    localSettings.trading?.paper_trading_mode ? 'translate-x-6' : 'translate-x-1'
                  }`} />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-gray-300">الحد الأقصى للصفقات اليومية</span>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={localSettings.trading?.max_daily_trades || 10}
                  onChange={(e) => updateLocalSetting('trading', 'max_daily_trades', parseInt(e.target.value))}
                  className="w-16 bg-gray-700 border border-gray-600 rounded px-2 py-1 text-white text-center"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  // Render current section
  const renderCurrentSection = () => {
    switch (activeSection) {
      case 'security':
        return renderSecuritySettings();
      case 'notifications':
        return renderNotificationSettings();
      case 'trading':
        return renderTradingSettings();
      case 'appearance':
        return <div className="glass-card p-6"><p className="text-gray-400">إعدادات المظهر قيد التطوير</p></div>;
      case 'general':
        return <div className="glass-card p-6"><p className="text-gray-400">الإعدادات العامة قيد التطوير</p></div>;
      default:
        return null;
    }
  };

  if (show2FASetup) {
    return <TwoFactorAuth onClose={() => setShow2FASetup(false)} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-purple-400 bg-clip-text text-transparent">
            إعدادات متقدمة
          </h1>
          <p className="text-gray-400 mt-2">تخصيص تجربة التداول والأمان</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <div className="glass-card p-4">
              <nav className="space-y-2">
                {sections.map((section) => {
                  const Icon = section.icon;
                  const isActive = activeSection === section.id;
                  
                  return (
                    <button
                      key={section.id}
                      onClick={() => setActiveSection(section.id)}
                      className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-right transition-all ${
                        isActive
                          ? `bg-gradient-to-r ${section.color} text-white shadow-lg`
                          : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
                      }`}
                    >
                      <Icon size={20} />
                      <span className="font-semibold">{section.name}</span>
                    </button>
                  );
                })}
              </nav>
            </div>
          </div>

          {/* Content */}
          <div className="lg:col-span-3">
            {renderCurrentSection()}
            
            {/* Save Button */}
            <div className="mt-6 flex justify-end">
              <button
                onClick={() => saveSettings()}
                disabled={loading[activeSection]}
                className="neon-button bg-gradient-to-r from-cyan-500 to-blue-500 hover:from-cyan-600 hover:to-blue-600 text-white font-semibold py-3 px-8 rounded-lg transition-all transform hover:scale-105 disabled:opacity-50"
              >
                {loading[activeSection] ? (
                  <div className="flex items-center gap-2">
                    <RefreshCw className="animate-spin" size={16} />
                    جاري الحفظ...
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <Save size={16} />
                    حفظ التغييرات
                  </div>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedSettings;