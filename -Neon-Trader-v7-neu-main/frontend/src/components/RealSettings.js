import React, { useState, useContext, useEffect } from 'react';
import { AppContext } from '../App';
import { 
  User, Shield, Bell, Palette, Database, Download, Upload, 
  Lock, Key, Clock, Smartphone, Globe, DollarSign, Bot,
  Save, RefreshCw, CheckCircle, XCircle, AlertTriangle
} from 'lucide-react';
import axios from 'axios';

const RealSettings = () => {
  const { showToast, currentUser } = useContext(AppContext);
  const [activeTab, setActiveTab] = useState('account');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  
  // Settings state with actual persistence
  const [settings, setSettings] = useState({
    // Account & Security
    username: currentUser?.username || '',
    email: currentUser?.email || '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
    twoFactorEnabled: false,
    autoLockMinutes: 5,
    sessionTimeoutMinutes: 15,
    
    // Trading & Risk
    defaultRiskPerTrade: 2.0,
    maxRiskPerTrade: 5.0,
    dailyLossLimit: 10.0,
    defaultStopLoss: 2.0,
    defaultTakeProfit: 6.0,
    enableOCO: true,
    enableTrailingStop: true,
    paperTradingMode: true,
    
    // AI Assistant
    aiProvider: 'emergent_llm',
    analysisFrequency: 'hourly',
    confidenceThreshold: 70,
    autoExecuteTrades: false,
    riskAnalysisEnabled: true,
    
    // Notifications
    enableNotifications: true,
    tradingAlerts: true,
    priceAlerts: true,
    systemAlerts: true,
    emailNotifications: false,
    
    // Appearance & Interface
    theme: 'dark-glass',
    language: 'ar',
    currency: 'USD',
    timezone: 'auto',
    chartTheme: 'dark',
    compactMode: false,
    
    // Platform Connections
    platforms: [],
    defaultPlatform: '',
    testnetMode: true
  });

  const tabs = [
    { id: 'account', name: 'الحساب والأمان', icon: User },
    { id: 'trading', name: 'التداول والمخاطر', icon: DollarSign },
    { id: 'ai', name: 'المساعد الذكي', icon: Bot },
    { id: 'platforms', name: 'المنصات', icon: Globe },
    { id: 'notifications', name: 'الإشعارات', icon: Bell },
    { id: 'appearance', name: 'المظهر والواجهة', icon: Palette },
    { id: 'backup', name: 'النسخ والاستيراد', icon: Database }
  ];

  // Load settings on component mount
  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      
      // Load user settings from backend
      const response = await axios.get('/user/settings');
      if (response.data) {
        setSettings(prevSettings => ({
          ...prevSettings,
          ...response.data,
          username: currentUser?.username || prevSettings.username,
          email: currentUser?.email || prevSettings.email
        }));
      }
      
      // Apply theme immediately
      applyThemeSettings();
      
    } catch (error) {
      console.error('Error loading settings:', error);
      // Use localStorage as fallback
      loadSettingsFromLocalStorage();
    } finally {
      setLoading(false);
    }
  };

  const loadSettingsFromLocalStorage = () => {
    try {
      const savedSettings = localStorage.getItem('neon_trader_settings');
      if (savedSettings) {
        const parsed = JSON.parse(savedSettings);
        setSettings(prevSettings => ({
          ...prevSettings,
          ...parsed,
          username: currentUser?.username || prevSettings.username,
          email: currentUser?.email || prevSettings.email
        }));
        applyThemeSettings(parsed);
      }
    } catch (error) {
      console.error('Error loading settings from localStorage:', error);
    }
  };

  const saveSettings = async () => {
    try {
      setSaving(true);
      
      // Validate settings
      if (settings.newPassword && settings.newPassword !== settings.confirmPassword) {
        showToast('كلمات المرور الجديدة غير متطابقة', 'error');
        return;
      }

      if (settings.maxRiskPerTrade > 10) {
        showToast('نسبة المخاطرة القصوى لا يمكن أن تزيد عن 10%', 'error');
        return;
      }

      // Prepare settings payload
      const settingsPayload = {
        ...settings,
        currentPassword: undefined, // Don't send passwords in settings
        newPassword: undefined,
        confirmPassword: undefined
      };

      // Save to backend
      try {
        await axios.put('/user/settings', settingsPayload);
        showToast('تم حفظ الإعدادات بنجاح', 'success');
      } catch (backendError) {
        console.warn('Backend save failed, using localStorage:', backendError);
        // Fallback to localStorage
        localStorage.setItem('neon_trader_settings', JSON.stringify(settingsPayload));
        showToast('تم حفظ الإعدادات محلياً', 'success');
      }

      // Handle password change separately
      if (settings.newPassword && settings.currentPassword) {
        try {
          await axios.put('/user/change-password', {
            currentPassword: settings.currentPassword,
            newPassword: settings.newPassword
          });
          showToast('تم تغيير كلمة المرور بنجاح', 'success');
          
          // Clear password fields
          setSettings(prev => ({
            ...prev,
            currentPassword: '',
            newPassword: '',
            confirmPassword: ''
          }));
        } catch (passwordError) {
          showToast('فشل في تغيير كلمة المرور', 'error');
        }
      }

      // Apply theme and other UI changes
      applyThemeSettings();
      
      setHasUnsavedChanges(false);
      
    } catch (error) {
      console.error('Error saving settings:', error);
      showToast('خطأ في حفظ الإعدادات', 'error');
    } finally {
      setSaving(false);
    }
  };

  const applyThemeSettings = (settingsToApply = settings) => {
    // Apply theme to document
    const root = document.documentElement;
    
    if (settingsToApply.theme === 'dark-glass') {
      root.setAttribute('data-theme', 'dark');
      document.body.classList.add('dark-glass');
    } else if (settingsToApply.theme === 'light') {
      root.setAttribute('data-theme', 'light');
      document.body.classList.remove('dark-glass');
    }

    // Apply language direction
    if (settingsToApply.language === 'ar') {
      document.dir = 'rtl';
      root.setAttribute('lang', 'ar');
    } else {
      document.dir = 'ltr';
      root.setAttribute('lang', 'en');
    }

    // Apply compact mode
    if (settingsToApply.compactMode) {
      document.body.classList.add('compact-mode');
    } else {
      document.body.classList.remove('compact-mode');
    }
  };

  const updateSetting = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
    setHasUnsavedChanges(true);
  };

  const testNotifications = async () => {
    try {
      if ('Notification' in window) {
        if (Notification.permission === 'granted') {
          new Notification('Neon Trader V7', {
            body: 'اختبار الإشعارات يعمل بنجاح!',
            icon: '/favicon.ico'
          });
          showToast('تم إرسال إشعار تجريبي', 'success');
        } else if (Notification.permission !== 'denied') {
          const permission = await Notification.requestPermission();
          if (permission === 'granted') {
            new Notification('Neon Trader V7', {
              body: 'تم تفعيل الإشعارات بنجاح!',
              icon: '/favicon.ico'
            });
            showToast('تم تفعيل الإشعارات', 'success');
          } else {
            showToast('تم رفض إذن الإشعارات', 'error');
          }
        } else {
          showToast('الإشعارات محجوبة في المتصفح', 'error');
        }
      } else {
        showToast('الإشعارات غير مدعومة في هذا المتصفح', 'error');
      }
    } catch (error) {
      console.error('Error testing notifications:', error);
      showToast('خطأ في اختبار الإشعارات', 'error');
    }
  };

  const exportSettings = () => {
    try {
      const exportData = {
        settings: settings,
        exportDate: new Date().toISOString(),
        version: '1.0.0'
      };
      
      const dataStr = JSON.stringify(exportData, null, 2);
      const dataBlob = new Blob([dataStr], {type: 'application/json'});
      
      const link = document.createElement('a');
      link.href = URL.createObjectURL(dataBlob);
      link.download = `neon-trader-settings-${new Date().toISOString().split('T')[0]}.json`;
      link.click();
      
      showToast('تم تصدير الإعدادات بنجاح', 'success');
    } catch (error) {
      console.error('Error exporting settings:', error);
      showToast('خطأ في تصدير الإعدادات', 'error');
    }
  };

  const importSettings = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const importData = JSON.parse(e.target.result);
        
        if (importData.settings) {
          setSettings(prev => ({
            ...prev,
            ...importData.settings,
            username: currentUser?.username || prev.username,
            email: currentUser?.email || prev.email,
            // Don't import password fields
            currentPassword: '',
            newPassword: '',
            confirmPassword: ''
          }));
          
          setHasUnsavedChanges(true);
          showToast('تم استيراد الإعدادات بنجاح', 'success');
        } else {
          showToast('ملف الإعدادات غير صالح', 'error');
        }
      } catch (error) {
        console.error('Error importing settings:', error);
        showToast('خطأ في قراءة ملف الإعدادات', 'error');
      }
    };
    
    reader.readAsText(file);
    // Reset file input
    event.target.value = '';
  };

  const renderAccountSettings = () => (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <User size={20} />
          معلومات الحساب
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">اسم المستخدم</label>
            <input
              type="text"
              value={settings.username}
              className="input-field"
              disabled
              title="لا يمكن تعديل اسم المستخدم"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">البريد الإلكتروني</label>
            <input
              type="email"
              value={settings.email}
              className="input-field"
              disabled
              title="لا يمكن تعديل البريد الإلكتروني"
            />
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Key size={20} />
          تغيير كلمة المرور
        </h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">كلمة المرور الحالية</label>
            <input
              type="password"
              value={settings.currentPassword}
              onChange={(e) => updateSetting('currentPassword', e.target.value)}
              className="input-field"
              placeholder="أدخل كلمة المرور الحالية"
            />
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">كلمة المرور الجديدة</label>
              <input
                type="password"
                value={settings.newPassword}
                onChange={(e) => updateSetting('newPassword', e.target.value)}
                className="input-field"
                placeholder="كلمة المرور الجديدة"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">تأكيد كلمة المرور</label>
              <input
                type="password"
                value={settings.confirmPassword}
                onChange={(e) => updateSetting('confirmPassword', e.target.value)}
                className="input-field"
                placeholder="أعد كتابة كلمة المرور"
              />
            </div>
          </div>
          
          {settings.newPassword && settings.confirmPassword && settings.newPassword !== settings.confirmPassword && (
            <div className="text-red-400 text-sm flex items-center gap-2">
              <XCircle size={16} />
              كلمات المرور غير متطابقة
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Shield size={20} />
          الأمان والحماية
        </h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-white font-medium">المصادقة الثنائية</label>
              <p className="text-sm text-gray-400">طبقة حماية إضافية لحسابك</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.twoFactorEnabled}
                onChange={(e) => updateSetting('twoFactorEnabled', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">القفل التلقائي (دقائق)</label>
              <select
                value={settings.autoLockMinutes}
                onChange={(e) => updateSetting('autoLockMinutes', parseInt(e.target.value))}
                className="input-field"
              >
                <option value={1}>دقيقة واحدة</option>
                <option value={5}>5 دقائق</option>
                <option value={10}>10 دقائق</option>
                <option value={30}>30 دقيقة</option>
                <option value={0}>بدون قفل تلقائي</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">انتهاء الجلسة (دقائق)</label>
              <select
                value={settings.sessionTimeoutMinutes}
                onChange={(e) => updateSetting('sessionTimeoutMinutes', parseInt(e.target.value))}
                className="input-field"
              >
                <option value={15}>15 دقيقة</option>
                <option value={30}>30 دقيقة</option>
                <option value={60}>ساعة واحدة</option>
                <option value={240}>4 ساعات</option>
                <option value={480}>8 ساعات</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderTradingSettings = () => (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <DollarSign size={20} />
          إدارة المخاطر
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                نسبة المخاطرة الافتراضية (%)
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={settings.defaultRiskPerTrade}
                  onChange={(e) => updateSetting('defaultRiskPerTrade', parseFloat(e.target.value))}
                  className="input-field"
                  min="0.1"
                  max="10"
                  step="0.1"
                />
                <span className="text-gray-400 text-sm">%</span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                أقصى مخاطرة في الصفقة (%)
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={settings.maxRiskPerTrade}
                  onChange={(e) => updateSetting('maxRiskPerTrade', parseFloat(e.target.value))}
                  className="input-field"
                  min="1"
                  max="10"
                  step="0.5"
                />
                <span className="text-gray-400 text-sm">%</span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                حد الخسارة اليومية (%)
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={settings.dailyLossLimit}
                  onChange={(e) => updateSetting('dailyLossLimit', parseFloat(e.target.value))}
                  className="input-field"
                  min="1"
                  max="20"
                  step="1"
                />
                <span className="text-gray-400 text-sm">%</span>
              </div>
            </div>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                وقف الخسارة الافتراضي (%)
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={settings.defaultStopLoss}
                  onChange={(e) => updateSetting('defaultStopLoss', parseFloat(e.target.value))}
                  className="input-field"
                  min="0.5"
                  max="10"
                  step="0.5"
                />
                <span className="text-gray-400 text-sm">%</span>
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                جني الأرباح الافتراضي (%)
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={settings.defaultTakeProfit}
                  onChange={(e) => updateSetting('defaultTakeProfit', parseFloat(e.target.value))}
                  className="input-field"
                  min="1"
                  max="20"
                  step="1"
                />
                <span className="text-gray-400 text-sm">%</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="text-white font-medium">وضع التداول التجريبي</label>
                <p className="text-sm text-gray-400">تداول بأموال افتراضية فقط</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.paperTradingMode}
                  onChange={(e) => updateSetting('paperTradingMode', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">ميزات التداول المتقدمة</h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-white font-medium">أوامر OCO</label>
              <p className="text-sm text-gray-400">One-Cancels-Other orders</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.enableOCO}
                onChange={(e) => updateSetting('enableOCO', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="text-white font-medium">وقف الخسارة المتحرك</label>
              <p className="text-sm text-gray-400">Trailing Stop Loss</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.enableTrailingStop}
                onChange={(e) => updateSetting('enableTrailingStop', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </div>
    </div>
  );

  const renderAISettings = () => (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Bot size={20} />
          إعدادات المساعد الذكي
        </h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">مقدم خدمة الذكاء الاصطناعي</label>
            <select
              value={settings.aiProvider}
              onChange={(e) => updateSetting('aiProvider', e.target.value)}
              className="input-field"
            >
              <option value="emergent_llm">Emergent LLM (موصى به)</option>
              <option value="gpt4">GPT-4 (خارجي)</option>
              <option value="claude">Claude (خارجي)</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">تكرار التحليل</label>
            <select
              value={settings.analysisFrequency}
              onChange={(e) => updateSetting('analysisFrequency', e.target.value)}
              className="input-field"
            >
              <option value="realtime">في الوقت الفعلي</option>
              <option value="5min">كل 5 دقائق</option>
              <option value="15min">كل 15 دقيقة</option>
              <option value="hourly">كل ساعة</option>
              <option value="daily">يومياً</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              عتبة الثقة (%): {settings.confidenceThreshold}
            </label>
            <input
              type="range"
              min="50"
              max="95"
              step="5"
              value={settings.confidenceThreshold}
              onChange={(e) => updateSetting('confidenceThreshold', parseInt(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>منخفض (50%)</span>
              <span>متوسط (70%)</span>
              <span>عالي (90%)</span>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="text-white font-medium">التنفيذ التلقائي للصفقات</label>
              <p className="text-sm text-gray-400">تنفيذ الصفقات المقترحة تلقائياً (محفوف بالمخاطر)</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.autoExecuteTrades}
                onChange={(e) => updateSetting('autoExecuteTrades', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="text-white font-medium">تحليل المخاطر المتقدم</label>
              <p className="text-sm text-gray-400">تحليل ذكي للمخاطر قبل كل صفقة</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.riskAnalysisEnabled}
                onChange={(e) => updateSetting('riskAnalysisEnabled', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>

          {settings.autoExecuteTrades && (
            <div className="bg-red-500/10 border border-red-500/30 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle size={20} className="text-red-400" />
                <span className="font-medium text-red-400">تحذير مهم</span>
              </div>
              <p className="text-sm text-red-300">
                التنفيذ التلقائي للصفقات قد يؤدي إلى خسائر مالية. استخدم هذه الميزة على مسؤوليتك الخاصة وتأكد من إعدادات إدارة المخاطر المناسبة.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  const renderNotificationSettings = () => (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Bell size={20} />
          إعدادات الإشعارات
        </h3>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <label className="text-white font-medium">تفعيل الإشعارات</label>
              <p className="text-sm text-gray-400">إشعارات المتصفح</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={testNotifications}
                className="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
              >
                اختبار
              </button>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.enableNotifications}
                  onChange={(e) => updateSetting('enableNotifications', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="text-white font-medium">تنبيهات التداول</label>
              <p className="text-sm text-gray-400">إشعارات تنفيذ الصفقات وإغلاقها</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.tradingAlerts}
                onChange={(e) => updateSetting('tradingAlerts', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="text-white font-medium">تنبيهات الأسعار</label>
              <p className="text-sm text-gray-400">إشعارات وصول الأسعار لمستويات معينة</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.priceAlerts}
                onChange={(e) => updateSetting('priceAlerts', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="text-white font-medium">تنبيهات النظام</label>
              <p className="text-sm text-gray-400">إشعارات التحديثات وحالة الاتصال</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.systemAlerts}
                onChange={(e) => updateSetting('systemAlerts', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>
          
          <div className="flex items-center justify-between">
            <div>
              <label className="text-white font-medium">الإشعارات عبر البريد الإلكتروني</label>
              <p className="text-sm text-gray-400">إرسال التنبيهات المهمة للبريد الإلكتروني</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={settings.emailNotifications}
                onChange={(e) => updateSetting('emailNotifications', e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
            </label>
          </div>
        </div>
      </div>
    </div>
  );

  const renderAppearanceSettings = () => (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Palette size={20} />
          المظهر والواجهة
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">سمة التطبيق</label>
              <select
                value={settings.theme}
                onChange={(e) => updateSetting('theme', e.target.value)}
                className="input-field"
              >
                <option value="dark-glass">داكن زجاجي (موصى به)</option>
                <option value="light">فاتح</option>
                <option value="dark">داكن كلاسيكي</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">اللغة</label>
              <select
                value={settings.language}
                onChange={(e) => updateSetting('language', e.target.value)}
                className="input-field"
              >
                <option value="ar">العربية</option>
                <option value="en">English</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">العملة الافتراضية</label>
              <select
                value={settings.currency}
                onChange={(e) => updateSetting('currency', e.target.value)}
                className="input-field"
              >
                <option value="USD">دولار أمريكي (USD)</option>
                <option value="EUR">يورو (EUR)</option>
                <option value="GBP">جنيه إسترليني (GBP)</option>
                <option value="SAR">ريال سعودي (SAR)</option>
                <option value="AED">درهم إماراتي (AED)</option>
              </select>
            </div>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">المنطقة الزمنية</label>
              <select
                value={settings.timezone}
                onChange={(e) => updateSetting('timezone', e.target.value)}
                className="input-field"
              >
                <option value="auto">تلقائي (حسب المتصفح)</option>
                <option value="UTC">UTC (توقيت عالمي)</option>
                <option value="America/New_York">نيويورك (EST/EDT)</option>
                <option value="Europe/London">لندن (GMT/BST)</option>
                <option value="Asia/Dubai">دبي (GST)</option>
                <option value="Asia/Riyadh">الرياض (AST)</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">سمة الرسوم البيانية</label>
              <select
                value={settings.chartTheme}
                onChange={(e) => updateSetting('chartTheme', e.target.value)}
                className="input-field"
              >
                <option value="dark">داكن</option>
                <option value="light">فاتح</option>
                <option value="professional">احترافي</option>
              </select>
            </div>
            
            <div className="flex items-center justify-between">
              <div>
                <label className="text-white font-medium">الوضع المضغوط</label>
                <p className="text-sm text-gray-400">واجهة أكثر إحكاماً لتوفير المساحة</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.compactMode}
                  onChange={(e) => updateSetting('compactMode', e.target.checked)}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
              </label>
            </div>
          </div>
        </div>

        <div className="mt-6 p-4 bg-blue-500/10 border border-blue-500/30 rounded-lg">
          <p className="text-sm text-blue-300">
            <strong>ملاحظة:</strong> بعض تغييرات المظهر قد تتطلب إعادة تحديث الصفحة لتظهر بشكل كامل.
          </p>
        </div>
      </div>
    </div>
  );

  const renderBackupSettings = () => (
    <div className="space-y-6">
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Database size={20} />
          النسخ الاحتياطي والاستيراد
        </h3>
        
        <div className="space-y-6">
          <div className="flex items-center justify-between p-4 border border-gray-600 rounded-lg">
            <div>
              <h4 className="font-medium text-white">تصدير الإعدادات</h4>
              <p className="text-sm text-gray-400">حفظ إعداداتك في ملف JSON</p>
            </div>
            <button
              onClick={exportSettings}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
            >
              <Download size={16} />
              تصدير
            </button>
          </div>
          
          <div className="flex items-center justify-between p-4 border border-gray-600 rounded-lg">
            <div>
              <h4 className="font-medium text-white">استيراد الإعدادات</h4>
              <p className="text-sm text-gray-400">استعادة إعداداتك من ملف محفوظ</p>
            </div>
            <div>
              <input
                type="file"
                accept=".json"
                onChange={importSettings}
                className="hidden"
                id="import-settings"
              />
              <label
                htmlFor="import-settings"
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors cursor-pointer"
              >
                <Upload size={16} />
                استيراد
              </label>
            </div>
          </div>

          <div className="bg-amber-500/10 border border-amber-500/30 p-4 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle size={20} className="text-amber-400" />
              <span className="font-medium text-amber-400">تنبيه مهم</span>
            </div>
            <ul className="text-sm text-amber-300 space-y-1">
              <li>• لن يتم تصدير كلمات المرور أو المفاتيح الحساسة</li>
              <li>• تأكد من حفظ الملف في مكان آمن</li>
              <li>• استيراد الإعدادات سيحل محل الإعدادات الحالية</li>
              <li>• احفظ الإعدادات بعد الاستيراد</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="p-4 fade-in">
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-400">جاري تحميل الإعدادات...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">إعدادات التطبيق</h1>
          <p className="text-gray-400 mt-1">إدارة تفضيلاتك وإعدادات التداول</p>
        </div>
        
        <div className="flex items-center gap-2">
          {hasUnsavedChanges && (
            <span className="text-amber-400 text-sm flex items-center gap-1">
              <AlertTriangle size={16} />
              تغييرات غير محفوظة
            </span>
          )}
          
          <button
            onClick={loadSettings}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            تحديث
          </button>
          
          <button
            onClick={saveSettings}
            disabled={saving || !hasUnsavedChanges}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              hasUnsavedChanges
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
            }`}
          >
            <Save size={16} className={saving ? 'animate-spin' : ''} />
            {saving ? 'جاري الحفظ...' : 'حفظ الإعدادات'}
          </button>
        </div>
      </div>

      {/* Settings Navigation */}
      <div className="flex overflow-x-auto gap-2 pb-2">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${
                activeTab === tab.id
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white'
                  : 'bg-white/10 text-gray-400 hover:text-white hover:bg-white/20'
              }`}
            >
              <Icon size={16} />
              {tab.name}
            </button>
          );
        })}
      </div>

      {/* Settings Content */}
      <div>
        {activeTab === 'account' && renderAccountSettings()}
        {activeTab === 'trading' && renderTradingSettings()}
        {activeTab === 'ai' && renderAISettings()}
        {activeTab === 'notifications' && renderNotificationSettings()}
        {activeTab === 'appearance' && renderAppearanceSettings()}
        {activeTab === 'backup' && renderBackupSettings()}
      </div>

      {/* Save Confirmation */}
      {hasUnsavedChanges && (
        <div className="fixed bottom-6 right-6 bg-amber-600 text-white p-4 rounded-lg shadow-lg flex items-center gap-3 z-50">
          <AlertTriangle size={20} />
          <span>لديك تغييرات غير محفوظة</span>
          <button
            onClick={saveSettings}
            className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded transition-colors"
          >
            حفظ الآن
          </button>
        </div>
      )}
    </div>
  );
};

export default RealSettings;